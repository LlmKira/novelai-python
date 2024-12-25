from pathlib import Path

from PIL import Image

from novelai_python.tool.image_metadata.lsb_extractor import ImageLsbDataExtractor

image = Path(__file__).parent.joinpath("sample-0316.png")
try:
    with Image.open(image) as img:
        data = ImageLsbDataExtractor().extract_data(img)
except ValueError:
    raise LookupError("Cant find a MetaData")

print(data)
