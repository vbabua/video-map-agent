import pixeltable as pxt
from PIL import Image


@pxt.udf
def extract_transcript_content(speech_transcript: pxt.type_system.Json) -> str:
    return f"{speech_transcript['text']}"


@pxt.udf
def scale_image(source_image: pxt.type_system.Image, target_width: int, target_height: int) -> pxt.type_system.Image:
    if not isinstance(source_image, Image.Image):
        raise TypeError("Input must be a PIL Image")

    source_image.thumbnail((target_width, target_height))
    return source_image