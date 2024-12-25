from pathlib import Path

from PIL import Image

from novelai_python.tool.image_metadata import ImageMetadata, ImageLsbDataExtractor, ImageVerifier

'''
    You can apply metadata to an image using the LSB method.
'''

image = Path(__file__).parent.joinpath("sample-0316.png")
write_out = Path(__file__).parent.joinpath("sample-0316-out.png")
try:
    with Image.open(image) as img:
        meta = ImageMetadata.load_image(img)
    with Image.open(image) as img:
        new_io = meta.apply_to_image(img, inject_lsb=True)
    with open(write_out, 'wb') as f:
        f.write(new_io.getvalue())
    with Image.open(write_out) as img:
        new_meta = ImageMetadata.load_image(img)
        data = ImageLsbDataExtractor().extract_data(img)
except ValueError:
    raise LookupError("Cant find a MetaData")
print(data)
print(new_meta)
print(new_meta.used_model)
with Image.open(write_out) as img:
    print(ImageVerifier().verify(img))
