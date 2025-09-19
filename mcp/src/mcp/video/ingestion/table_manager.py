import json
import os
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Dict

from loguru import logger

from mcp.video.ingestion.data_models import IndexedTable, IndexedTableInfo

logger = logger.bind(name="TableManager")

DEFAULT_STORED_TABLES_REGISTRY_PATH = ".storage_records"

MEDIA_INDEXES_STORAGE: Dict[str, IndexedTableInfo] = {}

@lru_cache(maxsize=1)
def get_table_registry() -> Dict[str, IndexedTableInfo]:
    """
    Get the media table registry, loading from the most recent JSON file if not already loaded.         
    Returns:
        Dict[str, IndexedTableInfo]: The media index registry.
    """

    global MEDIA_INDEXES_STORAGE
    if not MEDIA_INDEXES_STORAGE:
        try:
            registry_files = [
                f
                for f in os.listdir(DEFAULT_STORED_TABLES_REGISTRY_PATH)
                if f.startswith("registry_") and f.endswith(".json")
            ]
            if registry_files:
                most_recent_file = max(registry_files)
                most_recent_registry = Path(DEFAULT_STORED_TABLES_REGISTRY_PATH) / most_recent_file
                with open(str(most_recent_registry), "r") as f:
                    MEDIA_INDEXES_STORAGE = json.load(f)
                    for identifier, metadata in MEDIA_INDEXES_STORAGE.items():
                        if isinstance(metadata, str):
                            metadata = json.loads(metadata)
                        MEDIA_INDEXES_STORAGE[identifier] = IndexedTableInfo(**metadata)
                logger.info(f"Loaded registry from {most_recent_registry}")
        except FileNotFoundError:
            logger.warning("Registry path not found. Starting with an empty registry.")
    else:
        logger.info("Using existing media index registry.")
    return MEDIA_INDEXES_STORAGE


def register_new_index(
    media_identifier: str,
    storage_cache: str,
    visual_segments_name: str,
    sound_segments_name: str,
):
    """
    Register a new media index in the global registry and save to a JSON file.  
    Args:
        media_identifier (str): Unique identifier for the media.
        storage_cache (str): Path to the media cache.
        visual_segments_name (str): Name of the visual segments view.
        sound_segments_name (str): Name of the sound segments view.
    Returns:
        None
    Raises:
        IOError: If there are issues writing to the registry file.
    """
    global MEDIA_INDEXES_STORAGE
    indexed_table_info = IndexedTableInfo(
        media_identifier=media_identifier,
        storage_cache=storage_cache,
        content_table=f"{storage_cache}.content",
        visual_segments_view=visual_segments_name,
        sound_segments_view=sound_segments_name,
    ).model_dump_json()
    MEDIA_INDEXES_STORAGE[media_identifier] = indexed_table_info

    current_datetime = datetime.now()
    datetime_string = current_datetime.strftime("%Y-%m-%d%H:%M:%S")
    registry_directory = Path(DEFAULT_STORED_TABLES_REGISTRY_PATH)
    registry_directory.mkdir(parents=True, exist_ok=True)
    with open(registry_directory / f"registry_{datetime_string}.json", "w") as f:
        for key, value in MEDIA_INDEXES_STORAGE.items():
            if isinstance(value, IndexedTableInfo):
                value = value.model_dump_json()
            MEDIA_INDEXES_STORAGE[key] = value
        json.dump(MEDIA_INDEXES_STORAGE, f, indent=4)

    logger.info(f"Media index '{media_identifier}' registered in the global registry.")


def fetch_table(media_identifier: str) -> Dict[str, IndexedTable]:
    """
    Fetch an indexed media table by its identifier from the global registry.  
    Args:
        media_identifier (str): Unique identifier for the media.
    Returns:
        Dict[str, IndexedTable]: The indexed media table.
    Raises:
        KeyError: If the media identifier is not found in the registry."""
    table_registry = get_table_registry()
    logger.info(f"Registry: {table_registry}")
    table_info = table_registry.get(media_identifier)
    if isinstance(table_info, str):
        table_info = json.loads(table_info)
    logger.info(f"Table Info: {table_info}")
    return IndexedTable.from_info(table_info)