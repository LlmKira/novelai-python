from pathlib import Path

from novelai_python.tool.image_metadata import ImageMetadata, ImageLsbDataExtractor
from PIL import Image

image = Path(__file__).parent.joinpath("sample-0316.png")
write_out = Path(__file__).parent.joinpath("sample-0316-out.png")
try:
    meta = ImageMetadata.load_image(image)
    with Image.open(image) as img:
        new_io = meta.apply_to_image(img, inject_lsb=True)
        with open(write_out, 'wb') as f:
            f.write(new_io.getvalue())
    new_meta = ImageMetadata.load_image(write_out)
    data = ImageLsbDataExtractor().extract_data(write_out)
except ValueError:
    raise LookupError("Cant find a MetaData")
print(data)
print(new_meta)
print(new_meta.used_model)
print(ImageMetadata.verify_image_is_novelai(Image.open(write_out)))
