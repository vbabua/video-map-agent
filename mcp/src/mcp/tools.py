from typing import Dict
from uuid import uuid4

from loguru import logger

from mcp.config import get_settings
from mcp.media.ingestion.media_tools import create_media_clip
from mcp.media.ingestion.media_analyzer import MediaAnalyzer
from mcp.media.media_search_engine import MediaSearchEngine

logger = logger.bind(name="MCPMediaTools")
content_processor = MediaAnalyzer()
config = get_settings()


def analyze_media_content(content_path: str) -> str:
    """Process a media file and prepare it for searching.

    Args:
        content_path (str): Path to the media file to process.

    Returns:
        str: Success message indicating the media was processed.

    Raises:
        ValueError: If the media file cannot be found or processed.
    """
    already_exists = content_processor._verify_existence(content_path)
    if already_exists:
        logger.info(f"Media index for '{content_path}' already exists and is ready for use.")
        return False
    content_processor.initialize_storage(media_identifier=content_path)
    processing_complete = content_processor.insert_media(media_path=content_path)
    return processing_complete


def extract_clip_from_user_query(content_path: str, user_request: str) -> str:
    """Get a media clip based on the user query using speech and caption similarity.

    Args:
        content_path (str): The path to the media file.
        user_request (str): The user query to search for.

    Returns:
        str: Path to the extracted media clip.
    """
    search_handler = MediaSearchEngine(content_path)

    speech_matches = search_handler.find_by_speech_content(user_request, config.VIDEO_CLIP_SPEECH_SEARCH_TOP_K)
    description_matches = search_handler.find_by_description(user_request, config.VIDEO_CLIP_CAPTION_SEARCH_TOP_K)

    speech_confidence = speech_matches[0]["match_score"] if speech_matches else 0
    description_confidence = description_matches[0]["match_score"] if description_matches else 0

    selected_clip_info = speech_matches[0] if speech_confidence > description_confidence else description_matches[0]

    extracted_clip = create_media_clip(
        source_path=content_path,
        begin_time=selected_clip_info["begin_time"],
        finish_time=selected_clip_info["finish_time"],
        destination_path=f"./shared_media/{str(uuid4())}.mp4",
    )

    return extracted_clip.filename


def extract_clip_from_visual_query(content_path: str, query_image: str) -> str:
    """Get a media clip based on similarity to a provided image.

    Args:
        content_path (str): The path to the media file.
        query_image (str): The query image encoded in base64 format.

    Returns:
        str: Path to the extracted media clip.
    """
    search_handler = MediaSearchEngine(content_path)
    visual_matches = search_handler.find_by_visual_content(query_image, config.VIDEO_CLIP_IMAGE_SEARCH_TOP_K)

    extracted_clip = create_media_clip(
        source_path=content_path,
        begin_time=visual_matches[0]["begin_time"],
        finish_time=visual_matches[0]["finish_time"],
        destination_path=f"./shared_media/{str(uuid4())}.mp4",
    )

    return extracted_clip.filename


def answer_question_about_content(content_path: str, user_question: str) -> str:
    """Get relevant captions from the media based on the user's question.

    Args:
        content_path (str): The path to the media file.
        user_question (str): The question to search for relevant captions.

    Returns:
        str: Concatenated relevant captions from the media.
    """
    search_handler = MediaSearchEngine(content_path)
    description_details = search_handler.retrieve_description_details(user_question, config.QUESTION_ANSWER_TOP_K)

    response = "\n".join(item["description_text"] for item in description_details)
    return response