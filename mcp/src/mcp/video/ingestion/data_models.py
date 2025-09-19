import base64
import io
from typing import List, Literal, Union

import pixeltable as pxt
from PIL import Image
from pydantic import BaseModel, Field, field_validator

class IndexedTableInfo(BaseModel):
    """Metadata information for an indexed media table."""
    media_identifier: str = Field(..., description="Identifier of the media")
    storage_cache: str = Field(..., description="Path to the media cache")
    content_table: str = Field(..., description="Root media table")
    visual_segments_view: str = Field(..., description="Media frames which were split using a FPS and frame iterator")
    sound_segments_view: str = Field(
        ...,
        description="After chunking audio, getting transcript and splitting it into sentences",
    )


class IndexedTable:
    """Represents an indexed media table with its associated views."""
    storage_cache: str = Field(..., description="Path to the media cache")
    content_table: pxt.Table = Field(..., description="Root media table")
    visual_segments_view: pxt.Table = Field(..., description="Media frames which were split using a FPS and frame iterator")
    sound_segments_view: pxt.Table = Field(
        ...,
        description="After chunking audio, getting transcript and splitting it into sentences",
    )

    def __init__(
        self,
        media_identifier: str,
        storage_cache: str,
        content_table: pxt.Table,
        visual_segments_view: pxt.Table,
        sound_segments_view: pxt.Table,
    ):
        self.media_identifier = media_identifier
        self.storage_cache = storage_cache
        self.content_table = content_table
        self.visual_segments_view = visual_segments_view
        self.sound_segments_view = sound_segments_view

    @classmethod
    def from_info(cls, table_info: dict | IndexedTableInfo) -> "IndexedTable":
        """Create an IndexedTable instance from a dictionary or IndexedTableInfo object.
        Args:
            table_info (dict | IndexedTableInfo): The table information.
        Returns:
            IndexedTable: The constructed IndexedTable instance.
        """
        table_info = IndexedTableInfo(**table_info) if isinstance(table_info, dict) else table_info
        return cls(
            media_identifier=table_info.media_identifier,
            storage_cache=table_info.storage_cache,
            content_table=pxt.get_table(table_info.content_table),
            visual_segments_view=pxt.get_table(table_info.visual_segments_view),
            sound_segments_view=pxt.get_table(table_info.sound_segments_view),
        )

    def __str__(self):
        return {
            "storage_cache": self.storage_cache,
            "content_table": str(self.content_table),
            "visual_segments_view": str(self.visual_segments_view),
            "sound_segments_view": str(self.sound_segments_view),
        }

    def get_description(self) -> str:
        """
        Get a textual description of the indexed table.
        Returns:
            str: Description of the indexed table.  
        """
        return f"Media index '{self.media_identifier}' info: {', '.join(self.content_table.columns)}"

class EncodedImage(BaseModel):
    """Represents an image encoded as a base64 string."""
    image_data: str = Field(description="Base64 encoded image string")

    @field_validator("image_data", mode="before")
    def encode_image_data(cls, v):
        """Encode a PIL Image to a base64 string if necessary.
        Args:
            v (str | Image.Image): The image data, either as a base64 string or a PIL Image.
        Returns:
            str: Base64 encoded image string.
        Raises:
            TypeError: If the input is not a string or PIL Image.
        """
        if isinstance(v, Image.Image):
            buffer = io.BytesIO()
            v.save(buffer, format="JPEG")
            return base64.b64encode(buffer.getvalue()).decode("utf-8")
        return v

    def convert_to_pil(self) -> Image.Image:
        """Convert the base64 encoded image string back to a PIL Image."""
        return Image.open(io.BytesIO(base64.b64decode(self.image_data)))


class TextMessage(BaseModel):
    """Represents a text message."""
    content_type: Literal["text"] = "text"
    message_text: str


class ImageUrlMessage(BaseModel):
    """Represents an image message with a base64 encoded image URL."""
    content_type: Literal["image_url"] = "image_url"
    encoded_image: str = Field(..., serialization_alias="image_url")

    @field_validator("encoded_image", mode="before")
    def format_image_url(cls, v):
        """Format the image URL as a data URL if it's a base64 string.
        Args:
            v (str | dict): The image URL, either as a base64 string or a dictionary with 'url' key.
        Returns:
            str: Formatted image URL.
        Raises:
            TypeError: If the input is neither a string nor a dictionary with 'url' key"""
        if isinstance(v, str):
            return f"data:image/jpeg;base64,{v}"
        raise TypeError("image_url must be a dict with 'url' or a PIL Image")


class UserMessage(BaseModel):
    """Represents a user message containing text and an image."""
    role: Literal["user"] = "user"
    message_content: List[Union[TextMessage, ImageUrlMessage]]

    @classmethod
    def create_from_pair(cls, encoded_image: str, text_prompt: str):
        """Create a UserMessage instance from an image and text prompt.
        Args:
            encoded_image (str): Base64 encoded image string.
            text_prompt (str): The text prompt.
        Returns:        UserMessage: The constructed UserMessage instance.
            UserMessage: The constructed UserMessage instance.
        """
        return cls(
            message_content=[
                TextMessage(message_text=text_prompt),
                ImageUrlMessage(encoded_image=encoded_image),
            ]
        )