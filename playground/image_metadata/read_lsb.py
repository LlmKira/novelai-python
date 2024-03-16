import os
from pathlib import Path

from novelai_python.tool.image_metadata.lsb_extractor import ImageDataExtractor

image = Path(__file__).parent.joinpath("sample-0316.png")
try:
    data = ImageDataExtractor().extract_data(image)
except ValueError:
    raise LookupError("Cant find a MetaData")

print(data)
