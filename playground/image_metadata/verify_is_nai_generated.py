from pathlib import Path

from PIL import Image

from novelai_python.tool.image_metadata import ImageVerifier

image = Path(__file__).parent.joinpath("sample-0316.png")
try:
    with Image.open(image) as img:
        verify, have_latent = ImageVerifier().verify(image=img)
except ValueError:
    raise LookupError("Cant find a MetaData")

print(f"It is a NovelAI image: {verify}")
