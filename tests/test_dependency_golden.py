# Outputs recorded with the old dependencies (argon2-cffi, ftfy/regex CLIP tokenizer, OpenCV),
# kept to prove the pynacl / tokenizers / Pillow replacements give the same results.
import base64
import io
import json
import pathlib

import numpy as np
import pytest
from PIL import Image

from novelai_python.sdk.ai.generate_image.params import Params
from novelai_python.tool.paint_mask import create_mask_from_sketch
from novelai_python.utils.encode import encode_access_key

FIXTURES = pathlib.Path(__file__).parent / "fixtures"
GOLDEN = json.loads((FIXTURES / "dependency_golden.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize(("username", "password", "expected"), GOLDEN["access_keys"])
def test_access_key_matches_argon2_cffi(username, password, expected):
    assert encode_access_key(username, password) == expected


@pytest.mark.parametrize(("prompt", "expected"), GOLDEN["clip"])
def test_clip_ids_match_simple_tokenizer(prompt, expected):
    from novelai_python.tokenizer import NaiTokenizer

    tokenizer = NaiTokenizer("clip_tokenizer")
    assert tokenizer.encode(prompt) == expected
    if expected:
        assert tokenizer.decode(expected).strip()


@pytest.mark.parametrize("jagged", [True, False])
def test_mask_matches_opencv(jagged):
    ori = (FIXTURES / "mask_ori.png").read_bytes()
    sketch = (FIXTURES / "mask_sketch.png").read_bytes()
    mask = np.array(Image.open(io.BytesIO(create_mask_from_sketch(ori, sketch, jagged_edges=jagged))))
    white = mask > 127
    assert float(white.mean()) == pytest.approx(GOLDEN[f"mask_jagged_{jagged}_white_frac"], abs=0.01)
    bbox = np.argwhere(white).min(0).tolist() + np.argwhere(white).max(0).tolist()
    assert bbox == GOLDEN[f"mask_jagged_{jagged}_bbox"]


def test_black_background_pad_matches_opencv():
    rng = np.random.default_rng(0)
    rng.integers(0, 255, (96, 128, 3), dtype=np.uint8)  # the mask image drawn first in the recording
    img = rng.integers(0, 255, (50, 120, 3), dtype=np.uint8)
    buf = io.BytesIO()
    Image.fromarray(img, "RGB").save(buf, "PNG")
    padded = np.array(Image.open(io.BytesIO(base64.b64decode(Params.add_image_to_black_background(buf.getvalue())))))
    assert list(padded.shape) == GOLDEN["pad_shape"]
    assert int(padded[0, 0, 3]) == GOLDEN["pad_alpha_border"]
    # bilinear resize differs from cv2.INTER_LINEAR by rounding only
    assert float(padded[224, 100:348, :3].mean()) == pytest.approx(GOLDEN["pad_center_mean"], abs=1.0)
