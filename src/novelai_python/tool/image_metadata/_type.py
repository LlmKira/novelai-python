from io import BytesIO
from pathlib import Path
from typing import Union

IMAGE_INPUT_TYPE = Union[str, bytes, Path, BytesIO]


def get_image_bytes(image: IMAGE_INPUT_TYPE) -> BytesIO:
    if isinstance(image, (str, Path)):
        try:
            with open(image, "rb") as f:
                return BytesIO(f.read())
        except FileNotFoundError:
            raise FileNotFoundError(f"Image not found: {image}")
    elif isinstance(image, BytesIO):
        image.seek(0)
        return image
    elif isinstance(image, bytes):
        return BytesIO(image)
    else:
        raise TypeError(f"Invalid image type: {type(image)}, only {IMAGE_INPUT_TYPE} is supported")
