from typing import Any, Dict, List

import mcp.media.ingestion.table_manager as table_manager
from mcp.config import get_settings
from mcp.media.ingestion.data_models import IndexedTable
from mcp.media.ingestion.media_tools import convert_base64_to_image

config = get_settings()


class MediaSearchEngine:
    """A class that provides media search capabilities using different modalities."""

    def __init__(self, media_identifier: str):
        """Initialize the media search engine.

        Args:
            media_identifier (str): The name of the media index to search in.

        Raises:
            ValueError: If the media index is not found in registry.
        """
        self.media_index: IndexedTable = table_manager.fetch_table(media_identifier)
        if not self.media_index:
            raise ValueError(f"Media index {media_identifier} not found in registry.")
        self.media_identifier = media_identifier

    def find_by_speech_content(self, search_query: str, result_count: int) -> List[Dict[str, Any]]:
        """Search media clips by speech similarity.

        Args:
            search_query (str): The search query to match against speech content.
            result_count (int): Number of top results to return.

        Returns:
            List[Dict[str, Any]]: List of dictionaries containing clip information with keys:
                - begin_time (float): Start time in seconds
                - finish_time (float): End time in seconds
                - match_score (float): Similarity score
        """
        similarity_scores = self.media_index.sound_segments_view.segment_transcript.similarity(search_query)
        query_results = self.media_index.sound_segments_view.select(
            self.media_index.sound_segments_view.pos,
            self.media_index.sound_segments_view.start_time_sec,
            self.media_index.sound_segments_view.end_time_sec,
            match_score=similarity_scores,
        ).order_by(similarity_scores, asc=False)

        return [
            {
                "begin_time": float(record["start_time_sec"]),
                "finish_time": float(record["end_time_sec"]),
                "match_score": float(record["match_score"]),
            }
            for record in query_results.limit(result_count).collect()
        ]

    def find_by_visual_content(self, encoded_image: str, result_count: int) -> List[Dict[str, Any]]:
        """Search media clips by image similarity.

        Args:
            encoded_image (str): The query image to match against media frames.
            result_count (int): Number of top results to return.

        Returns:
            List[Dict[str, Any]]: List of dictionaries containing clip information with keys:
                - begin_time (float): Start time in seconds
                - finish_time (float): End time in seconds
                - match_score (float): Similarity score
        """
        query_image = convert_base64_to_image(encoded_image)
        similarity_scores = self.media_index.visual_segments_view.scaled_visual.similarity(query_image)
        query_results = self.media_index.visual_segments_view.select(
            self.media_index.visual_segments_view.pos_msec,
            self.media_index.visual_segments_view.scaled_visual,
            match_score=similarity_scores,
        ).order_by(similarity_scores, asc=False)

        return [
            {
                "begin_time": record["pos_msec"] / 1000.0 - config.FRAME_TIME_BUFFER,
                "finish_time": record["pos_msec"] / 1000.0 + config.FRAME_TIME_BUFFER,
                "match_score": float(record["match_score"]),
            }
            for record in query_results.limit(result_count).collect()
        ]

    def find_by_description(self, search_query: str, result_count: int) -> List[Dict[str, Any]]:
        """Search media clips by caption similarity.

        Args:
            search_query (str): The search query to match against frame captions.
            result_count (int): Number of top results to return.

        Returns:
            List[Dict[str, Any]]: List of dictionaries containing clip information with keys:
                - begin_time (float): Start time in seconds
                - finish_time (float): End time in seconds
                - match_score (float): Similarity score
        """
        similarity_scores = self.media_index.visual_segments_view.visual_description.similarity(search_query)
        query_results = self.media_index.visual_segments_view.select(
            self.media_index.visual_segments_view.pos_msec,
            self.media_index.visual_segments_view.visual_description,
            match_score=similarity_scores,
        ).order_by(similarity_scores, asc=False)

        return [
            {
                "begin_time": record["pos_msec"] / 1000.0 - config.FRAME_TIME_BUFFER,
                "finish_time": record["pos_msec"] / 1000.0 + config.FRAME_TIME_BUFFER,
                "match_score": float(record["match_score"]),
            }
            for record in query_results.limit(result_count).collect()
        ]

    def retrieve_speech_details(self, search_query: str, result_count: int) -> List[Dict[str, Any]]:
        """Get speech text information based on query similarity.

        Args:
            search_query (str): The search query to match against speech content.
            result_count (int): Number of top results to return.

        Returns:
            List[Dict[str, Any]]: List of dictionaries containing text information with keys:
                - transcript_text (str): The speech text
                - match_score (float): Similarity score
        """
        similarity_scores = self.media_index.sound_segments_view.segment_transcript.similarity(search_query)
        query_results = self.media_index.sound_segments_view.select(
            self.media_index.sound_segments_view.segment_transcript,
            match_score=similarity_scores,
        ).order_by(similarity_scores, asc=False)

        return [
            {
                "transcript_text": record["segment_transcript"],
                "match_score": float(record["match_score"]),
            }
            for record in query_results.limit(result_count).collect()
        ]

    def retrieve_description_details(self, search_query: str, result_count: int) -> List[Dict[str, Any]]:
        """Get caption information based on query similarity.

        Args:
            search_query (str): The search query to match against frame captions.
            result_count (int): Number of top results to return.

        Returns:
            List[Dict[str, Any]]: List of dictionaries containing caption information with keys:
                - description_text (str): The frame caption
                - match_score (float): Similarity score
        """
        similarity_scores = self.media_index.visual_segments_view.visual_description.similarity(search_query)
        query_results = self.media_index.visual_segments_view.select(
            self.media_index.visual_segments_view.visual_description,
            match_score=similarity_scores,
        ).order_by(similarity_scores, asc=False)

        return [
            {
                "description_text": record["visual_description"],
                "match_score": float(record["match_score"]),
            }
            for record in query_results.limit(result_count).collect()
        ]