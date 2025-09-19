


import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import pixeltable as pxt
from loguru import logger
from pixeltable.functions import openai
from pixeltable.functions.huggingface import clip
from pixeltable.functions.openai import embeddings, vision
from pixeltable.functions.video import extract_audio
from pixeltable.iterators import AudioSplitter
from pixeltable.iterators.video import FrameIterator

import mcp.video.ingestion.table_manager as table_manager
from mcp.config import get_settings
from mcp.video.ingestion.utilities import extract_transcript_content, scale_image
from mcp.video.ingestion.media_tools import transcode_media_file

if TYPE_CHECKING:
    from mcp.video.ingestion.data_models import IndexedTable

logger = logger.bind(name="MediaAnalyzer")
config = get_settings()


class MediaAnalyzer:
    def __init__(
        self,
    ):
        self._cache_directory: Optional[str] = None
        self._media_table = None
        self._visual_segments_view = None
        self._sound_segments = None
        self._index_mapping_key: Optional[str] = None

        logger.info(
            "MediaAnalyzer initialized",
            f"\n Frame Rate: {config.FRAME_EXTRACTION_RATE}",
            f"\n Sound Segment Duration: {config.SOUND_SEGMENT_DURATION} seconds",
        )

    def initialize_storage(self, media_identifier: str):
        """ 
        Initialize storage structures for media analysis.
        Args:
            media_identifier (str): Unique identifier for the media.    
        Raises:
            ValueError: If media_identifier is empty.
        """
        if not media_identifier:
            raise ValueError("Media identifier cannot be empty.")
        self._index_mapping_key = media_identifier
        table_exists = self._verify_existence(media_identifier)
        if table_exists:
            logger.info(f"Media index '{self._index_mapping_key}' already exists and is ready for use.")
            indexed_table: "IndexedTable" = table_manager.fetch_table(self._index_mapping_key)
            self.cache_directory = indexed_table.storage_cache
            self.media_table = indexed_table.content_table
            self.visual_segments_view = indexed_table.visual_segments_view
            self.sound_segments = indexed_table.sound_segments_view

        else:
            self.cache_directory = f"storage_{uuid.uuid4().hex[-4:]}"
            self.content_table_name = f"{self.cache_directory}.content"
            self.visual_segments_name = f"{self.content_table_name}_visuals"
            self.sound_segments_name = f"{self.content_table_name}_audio_parts"
            self.media_table = None

            self._initialize_storage_structure()

            table_manager.register_new_index(
                media_identifier=self._index_mapping_key,
                storage_cache=self.cache_directory,
                visual_segments_name=self.visual_segments_name,
                sound_segments_name=self.sound_segments_name,
            )
            logger.info(f"Creating new media index '{self.content_table_name}' in '{self.cache_directory}'")

    def _verify_existence(self, media_path: str) -> bool:
        """
        Checks if the PixelTable and related views/index for the media index exist.
        Returns:
            bool: True if current media index exists, False otherwise.
        """
        registered_tables = table_manager.get_table_registry()
        return media_path in registered_tables

    def _initialize_storage_structure(self):
        self._create_cache_location()
        self._build_content_table()
        self._configure_sound_analysis()
        self._configure_visual_analysis()

    def _create_cache_location(self):
        logger.info(f"Creating storage path {self.cache_directory}.")
        Path(self.cache_directory).mkdir(parents=True, exist_ok=True)
        pxt.create_dir(self.cache_directory, if_exists="replace_force")

    def _build_content_table(self):
        self.media_table = pxt.create_table(
            self.content_table_name,
            schema={"media_file": pxt.Video},
            if_exists="replace_force",
        )

    def _configure_sound_analysis(self):
        self.media_table.add_computed_column(
            sound_extraction=extract_audio(self.media_table.media_file, format="mp3"),
            if_exists="ignore",
        )

        self.sound_segments = pxt.create_view(
            self.sound_segments_name,
            self.media_table,
            iterator=AudioSplitter.create(
                audio=self.media_table.sound_extraction,
                chunk_duration_sec=config.SOUND_SEGMENT_DURATION,
                overlap_sec=config.SOUND_OVERLAP_DURATION,
                min_chunk_duration_sec=config.MIN_SOUND_SEGMENT_LENGTH,
            ),
            if_exists="replace_force",
        )
        
        self.sound_segments.add_computed_column(
            speech_to_text=openai.transcriptions(
                audio=self.sound_segments.audio_chunk,
                model=config.SPEECH_TRANSCRIPTION_MODEL,
            ),
            if_exists="ignore",
        )
        
        self.sound_segments.add_computed_column(
            segment_transcript=extract_transcript_content(self.sound_segments.speech_to_text),
            if_exists="ignore",
        )

        self.sound_segments.add_embedding_index(
            column=self.sound_segments.segment_transcript,
            string_embed=embeddings.using(model=config.TRANSCRIPT_SIMILARITY_EMBD_MODEL),
            if_exists="ignore",
            idx_name="transcript_index",
        )

    def _configure_visual_analysis(self):
        self.visual_segments_view = pxt.create_view(
            self.visual_segments_name,
            self.media_table,
            iterator=FrameIterator.create(video=self.media_table.media_file, num_frames=config.FRAME_EXTRACTION_RATE),
            if_exists="ignore",
        )
        self.visual_segments_view.add_computed_column(
            scaled_visual=scale_image(
                self.visual_segments_view.frame,
                target_width=config.IMAGE_RESIZE_WIDTH,
                target_height=config.IMAGE_RESIZE_HEIGHT,
            )
        )
        self.visual_segments_view.add_embedding_index(
            column=self.visual_segments_view.scaled_visual,
            image_embed=clip.using(model_id=config.IMAGE_SIMILARITY_EMBEDDING_MODEL),
            if_exists="replace_force",
        )
        self.visual_segments_view.add_computed_column(
            visual_description=vision(
                prompt=config.CAPTION_MODEL_PROMPT,
                image=self.visual_segments_view.scaled_visual,
                model=config.VISUAL_CAPTION_MODEL,
            )
        )
        self.visual_segments_view.add_embedding_index(
            column=self.visual_segments_view.visual_description,
            string_embed=embeddings.using(model=config.CAPTION_SIMILARITY_EMBEDDING_MODEL),
            if_exists="replace_force",
        )

        
    def insert_media(self, media_path: str) -> bool:
        """
        Add a media file to the pixel table.

        Args:
            media_path (str): The path to the media file.
        """
        if not self.media_table:
            raise ValueError("Media table is not initialized. Call initialize_storage() first.")
        logger.info(f"Adding media {media_path} to table {self.content_table_name}")

        processed_media_path = transcode_media_file(file_path=media_path)
        if processed_media_path:
            self.media_table.insert([{"media_file": media_path}])
        return True