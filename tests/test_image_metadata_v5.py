# A real V5 image straight from /ai/generate-image (WebP, recompressed losslessly with
# identical pixels and the original EXIF block).
import pathlib

import numpy as np
from PIL import Image

from novelai_python.tool.image_metadata import ImageMetadata, ImageVerifier

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "v5_signed.webp"


def test_v5_signature_over_masked_rgba_verifies():
    # V5 signs RGBA with the alpha LSB cleared; checking RGB only rejected every V5 image
    assert ImageVerifier().verify(Image.open(FIXTURE)) == (True, False)


def test_v5_signature_rejects_changed_pixel():
    arr = np.array(Image.open(FIXTURE))
    arr[100, 100, 0] ^= 0x40
    assert ImageVerifier().verify(Image.fromarray(arr, "RGBA"))[0] is False


def test_v5_webp_exif_metadata_matches_alpha():
    img = Image.open(FIXTURE)
    exif = ImageMetadata.load_from_pnginfo(img)
    alpha = ImageMetadata.load_from_watermark(img)
    assert exif.Source == "NovelAI Diffusion V5 0ADF9AB7"
    assert exif.Title == "AI generated image"
    assert exif.Comment is not None and alpha.Comment is not None
    assert exif.Comment.model_dump() == alpha.Comment.model_dump()
    assert exif.Comment.steps == 28
    assert exif.Generation_time is not None


def test_png_without_comment_reports_no_metadata():
    import io

    import pytest

    buf = io.BytesIO()
    Image.new("RGB", (8, 8)).save(buf, "PNG")
    with pytest.raises(ValueError, match="No metadata"):
        ImageMetadata.load_from_pnginfo(Image.open(io.BytesIO(buf.getvalue())))
