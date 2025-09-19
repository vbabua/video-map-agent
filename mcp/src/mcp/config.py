from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="mcp/.env", extra="ignore", env_file_encoding="utf-8")

    OPIK_API_KEY: str
    OPIK_WORKSPACE: str = "default"
    OPIK_PROJECT: str = "mcp"

    OPENAI_API_KEY: str
    SPEECH_TRANSCRIPTION_MODEL: str = "gpt-4o-mini-transcribe" 
    VISUAL_CAPTION_MODEL: str = "gpt-4o-mini"

    FRAME_EXTRACTION_RATE: int = 45
    SOUND_SEGMENT_DURATION: int = 10
    SOUND_OVERLAP_DURATION: int = 1
    MIN_SOUND_SEGMENT_LENGTH: int = 1

    TRANSCRIPT_SIMILARITY_EMBD_MODEL: str = "text-embedding-3-small"

    IMAGE_SIMILARITY_EMBEDDING_MODEL: str = "openai/clip-vit-base-patch32"

    IMAGE_RESIZE_WIDTH: int = 1024
    IMAGE_RESIZE_HEIGHT: int = 768
    CAPTION_SIMILARITY_EMBEDDING_MODEL: str = "text-embedding-3-small"

    CAPTION_MODEL_PROMPT: str = "Describe what is happening in the image"
    DELTA_SECONDS_FRAME_INTERVAL: float = 5.0

    VIDEO_CLIP_SPEECH_SEARCH_TOP_K: int = 1
    VIDEO_CLIP_CAPTION_SEARCH_TOP_K: int = 1
    VIDEO_CLIP_IMAGE_SEARCH_TOP_K: int = 1
    QUESTION_ANSWER_TOP_K: int = 3


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Get the application settings, cached for efficiency.
    Returns:
        Settings: The application settings.
    """
    return Settings()
