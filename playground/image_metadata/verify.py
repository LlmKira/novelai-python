import os
from pathlib import Path

from PIL import Image

from novelai_python.tool.image_metadata import ImageMetadata

image = Path(__file__).parent.joinpath("sample-0316.png")
try:
    verify = ImageMetadata.verify_image_is_novelai(Image.open(image))
except ValueError:
    raise LookupError("Cant find a MetaData")

print(f"It is a NovelAI image: {verify}")
