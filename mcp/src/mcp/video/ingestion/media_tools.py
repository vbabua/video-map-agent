import base64
import subprocess
from io import BytesIO
from pathlib import Path

import av
import loguru
from moviepy import VideoFileClip
from PIL import Image

logger = loguru.logger.bind(name="MediaTools")


def create_media_clip(source_path: str, begin_time: float, finish_time: float, destination_path: str = None) -> VideoFileClip:
    """
    Create a video clip from a source video file between specified start and end times.
    Args:
        source_path (str): Path to the source video file.
        begin_time (float): Start time in seconds for the clip.
        finish_time (float): End time in seconds for the clip.
        destination_path (str, optional): Path to save the output clip. If None, a temporary file will be created.
    Returns:
        VideoFileClip: The resulting video clip object.
    Raises:
        ValueError: If begin_time is not less than finish_time.
        IOError: If there are issues during the clip creation process.
    """
    if begin_time >= finish_time:
        raise ValueError("begin_time must be less than finish_time")
    ffmpeg_command = [
        "ffmpeg",
        "-ss",
        str(begin_time),
        "-to",
        str(finish_time),
        "-i",
        source_path,
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "23",
        "-c:a",
        "copy",
        "-y",
        destination_path,
    ]

    try:
        execution_process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output_data, _ = execution_process.communicate()
        logger.debug(f"FFmpeg output: {output_data.decode('utf-8', errors='ignore')}")
        return VideoFileClip(destination_path)
    except subprocess.CalledProcessError as e:
        raise IOError(f"Failed to create media clip: {str(e)}")


def convert_image_to_base64(source_image: str | Image.Image) -> str:
    """
    Convert a PIL Image object or image file path to a base64 encoded string.   
    Args:
        source_image (str | Image.Image): PIL Image object or path to the image file.
    Returns:
        str: Base64 encoded string representation of the image.
    Raises:
        TypeError: If the input is neither a string nor a PIL Image.
        IOError: If there are issues processing the image file.
    """
    try:
        if isinstance(source_image, str):
            with open(source_image, "rb") as image_file:
                binary_data = image_file.read()
        else:
            if not source_image.format:
                output_format = "JPEG"
            else:
                output_format = source_image.format

            memory_buffer = BytesIO()
            source_image.save(memory_buffer, format=output_format)
            binary_data = memory_buffer.getvalue()

        return base64.b64encode(binary_data).decode("utf-8")

    except (FileNotFoundError, IOError) as e:
        raise IOError(f"Failed to process image: {str(e)}")


def convert_base64_to_image(encoded_string: str) -> Image.Image:
    """
    Convert a base64 encoded string back to a PIL Image object.   
    Args:
        encoded_string (str): Base64 encoded string representation of the image.
    Returns:
        Image.Image: The resulting PIL Image object.
    Raises:
        IOError: If there are issues decoding the base64 string or processing the image data.   
    """
    try:
        binary_image_data = base64.b64decode(encoded_string)
        buffer_stream = BytesIO(binary_image_data)

        return Image.open(buffer_stream)

    except (ValueError, IOError) as e:
        raise IOError(f"Failed to decode image: {str(e)}")


def transcode_media_file(file_path: str) -> str:
    """
    Transcode a media file to ensure compatibility using FFmpeg if necessary.   
    Args:
        file_path (str): Path to the media file.
    Returns:
        str: Path to the original or transcoded media file if successful, else None.
    Raises:
        IOError: If there are issues during the transcoding process.    
    """
    if not Path(file_path).exists():
        logger.error(f"Error: Media file not found at {file_path}")
        return False

    try:
        with av.open(file_path) as _:
            logger.info(f"Media {file_path} successfully opened by PyAV.")
            return str(file_path)
    except Exception as e:
        logger.error(f"An unexpected error occurred while trying to open media {file_path}: {e}")
    finally:
        source_directory, source_filename = Path(file_path).parent, Path(file_path).name
        transcoded_name = f"transcoded_{source_filename}"
        transcoded_file_path = Path(source_directory) / transcoded_name

        transcoding_command = ["ffmpeg", "-i", file_path, "-c", "copy", str(transcoded_file_path)]

        logger.info(f"Attempting to transcode media using FFmpeg: {' '.join(transcoding_command)}")

        try:
            execution_result = subprocess.run(transcoding_command, capture_output=True, text=True, check=True)
            logger.info(f"FFmpeg transcoding successful for {file_path} to {transcoded_file_path}")
            logger.debug(f"FFmpeg stdout: {execution_result.stdout}")
            logger.debug(f"FFmpeg stderr: {execution_result.stderr}")

            try:
                with av.open(transcoded_file_path) as _:
                    logger.info(f"Transcoded media {transcoded_file_path} successfully opened by PyAV.")
                    return str(transcoded_file_path)
            except Exception as e:
                logger.error(
                    f"An unexpected error occurred while trying to open transcoded media {transcoded_file_path}: {e}"
                )
                return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during FFmpeg transcoding: {e}")
            return None