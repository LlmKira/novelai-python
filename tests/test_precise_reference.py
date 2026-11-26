"""Precise Reference request fields, as the novelai.net web client builds them for V4.5 and V5."""

import base64
import io

import numpy as np
import pytest
from PIL import Image

from novelai_python import CharacterReference, GenerateImageInfer
from novelai_python.sdk.ai._enum import Model
from novelai_python.sdk.ai.generate_image.schema import DIRECTOR_BUCKETS

# The bucket table of the web client bundle, as it is there
WEB_CLIENT_BUCKETS = [
    [256, 4096], [256, 4032], [256, 3968], [256, 3904], [256, 3840], [256, 3776], [256, 3712], [256, 3648],
    [256, 3584], [256, 3520], [256, 3456], [256, 3392], [256, 3328], [320, 3264], [320, 3200], [320, 3136],
    [320, 3072], [320, 3008], [320, 2944], [320, 2880], [320, 2816], [320, 2752], [384, 2688], [384, 2624],
    [384, 2560], [384, 2496], [384, 2432], [384, 2368], [448, 2304], [448, 2240], [448, 2176], [448, 2112],
    [512, 2048], [512, 1984], [512, 1920], [512, 1856], [576, 1792], [576, 1728], [576, 1664], [640, 1600],
    [640, 1536], [704, 1472], [704, 1408], [768, 1344], [768, 1280], [832, 1216], [896, 1152], [960, 1088],
    [1024, 1024], [1088, 960], [1152, 896], [1216, 832], [1280, 768], [1344, 768], [1408, 704], [1472, 704],
    [1536, 640], [1600, 640], [1664, 576], [1728, 576], [1792, 576], [1856, 512], [1920, 512], [1984, 512],
    [2048, 512], [2112, 448], [2176, 448], [2240, 448], [2304, 448], [2368, 384], [2432, 384], [2496, 384],
    [2560, 384], [2624, 384], [2688, 384], [2752, 320], [2816, 320], [2880, 320], [2944, 320], [3008, 320],
    [3072, 320], [3136, 320], [3200, 320], [3264, 320], [3328, 256], [3392, 256], [3456, 256], [3520, 256],
    [3584, 256], [3648, 256], [3712, 256], [3776, 256], [3840, 256], [3904, 256], [3968, 256], [4032, 256],
    [4096, 256],
]  # fmt: skip


def _png(width, height, color=(255, 0, 0), mode="RGB") -> bytes:
    buf = io.BytesIO()
    Image.new(mode, (width, height), color).save(buf, "PNG")
    return buf.getvalue()


def _size(b64: str) -> tuple[int, int]:
    return Image.open(io.BytesIO(base64.b64decode(b64))).size


def _params(gen: GenerateImageInfer) -> dict:
    return gen.parameters.model_dump(mode="json", exclude_none=True)


def _captions(p: dict) -> list[str]:
    return [d["caption"]["base_caption"] for d in p["director_reference_descriptions"]]


def test_v5_buckets_are_the_web_client_table():
    assert [list(b) for b in DIRECTOR_BUCKETS] == WEB_CLIENT_BUCKETS


@pytest.mark.parametrize(
    ("size", "bucket"),
    [
        ((300, 600), (704, 1408)),
        ((800, 400), (1408, 704)),
        ((1000, 1000), (1024, 1024)),
        ((1200, 1000), (1088, 960)),  # covers 1152 x 960, cropped 32 px each side
        ((100, 4000), (256, 4096)),
    ],
)
def test_v5_reference_is_cropped_to_the_closest_bucket(size, bucket):
    gen = GenerateImageInfer.build_generate(
        "1girl", model=Model.NAI_DIFFUSION_5_FULL, character_references=[CharacterReference(image=_png(*size))]
    )
    assert _size(_params(gen)["director_reference_images"][0]) == bucket


def test_v5_reference_of_a_bucket_size_is_sent_as_it_is():
    raw = _png(832, 1216)
    gen = GenerateImageInfer.build_generate(
        "1girl", model=Model.NAI_DIFFUSION_5_CURATED, character_references=[CharacterReference(image=raw)]
    )
    assert base64.b64decode(_params(gen)["director_reference_images"][0]) == raw


def test_v5_crop_keeps_the_centre():
    image = Image.new("RGB", (1200, 1000), (0, 0, 255))
    image.paste((255, 0, 0), (0, 0, 60, 1000))  # a red band on the left edge, partly cropped away
    buf = io.BytesIO()
    image.save(buf, "PNG")
    out = CharacterReference(image=buf.getvalue()).bucketed_image_b64()
    cropped = Image.open(io.BytesIO(base64.b64decode(out))).convert("RGB")
    assert cropped.size == (1088, 960)
    assert cropped.getpixel((0, 480))[0] > 200  # 60 px scaled by 0.96 is 57.6, 32 px of it cut off
    assert cropped.getpixel((544, 480)) == (0, 0, 255)


def test_descriptions_and_fidelity_follow_the_model():
    refs = [
        CharacterReference(image=_png(64, 64), description="character_mainoutfit", fidelity=0.75),
        CharacterReference(image=_png(64, 64), description="character&style_anyoutfit", fidelity=0.75),
        CharacterReference(image=_png(64, 64), description="costume", fidelity=0.75),
        CharacterReference(image=_png(64, 64), description="style", fidelity=0.75),
    ]
    v5 = _params(
        GenerateImageInfer.build_generate("1girl", model=Model.NAI_DIFFUSION_5_FULL, character_references=refs)
    )
    assert _captions(v5) == ["character_mainoutfit", "character&style_anyoutfit", "costume", "style"]
    assert v5["director_reference_secondary_strength_values"] == [0, 0, 0, 0]  # no Fidelity on V5

    with pytest.warns(UserWarning, match="nai-diffusion-4-5-full takes no outfit reference: 1 left out") as caught:
        v45 = _params(
            GenerateImageInfer.build_generate("1girl", model=Model.NAI_DIFFUSION_4_5_FULL, character_references=refs)
        )
    assert caught[0].filename == __file__  # points at the caller, not into the library
    # no outfits on V4.5: the outfit reference is left out, the outfit variants fold back
    assert _captions(v45) == ["character", "character&style", "style"]
    assert v45["director_reference_secondary_strength_values"] == [0.25, 0.25, 0.25]
    assert [_size(b) for b in v45["director_reference_images"]] == [(1472, 1472)] * 3


def test_strength_goes_past_the_slider():
    refs = [
        CharacterReference(image=_png(64, 64), strength=5.6),
        CharacterReference(image=_png(64, 64), strength=-1.2, description="style"),
    ]
    p = _params(GenerateImageInfer.build_generate("1girl", model=Model.NAI_DIFFUSION_5_FULL, character_references=refs))
    assert p["director_reference_strength_values"] == [5.6, -1.2]
    with pytest.raises(ValueError):
        CharacterReference(image=_png(8, 8), strength=float("nan"))


def test_medium_needs_high_effort():
    with pytest.raises(
        ValueError, match="High effort: use nai-diffusion-5-full instead of nai-diffusion-5-full-medium"
    ):
        GenerateImageInfer.build_generate(
            "1girl",
            model=Model.NAI_DIFFUSION_5_FULL_MEDIUM,
            character_references=[CharacterReference(image=_png(8, 8))],
        )


@pytest.mark.parametrize("model", [Model.NAI_DIFFUSION_3, Model.NAI_DIFFUSION_4_FULL])
def test_older_models_take_no_reference(model):
    with pytest.raises(ValueError, match=f"{model.value} takes no Precise Reference"):
        GenerateImageInfer.build_generate(
            "1girl", model=model, character_references=[CharacterReference(image=_png(8, 8))]
        )


def test_v5_full_takes_no_reference_when_inpainting():
    with pytest.raises(ValueError, match=r"nai-diffusion-5-full-inpainting takes no Precise Reference when inpainting"):
        GenerateImageInfer.build_infill(
            "1girl",
            model=Model.NAI_DIFFUSION_5_FULL,
            image=_png(832, 1216),
            mask=_png(832, 1216, (255, 255, 255)),
            character_references=[CharacterReference(image=_png(64, 64))],
        )


def test_v5_curated_inpaints_with_v45_references():
    with pytest.warns(UserWarning, match="nai-diffusion-4-5-curated-inpainting takes no outfit reference"):
        gen = GenerateImageInfer.build_infill(
            "1girl",
            model=Model.NAI_DIFFUSION_5_CURATED,
            image=_png(832, 1216),
            mask=_png(832, 1216, (255, 255, 255)),
            character_references=[
                CharacterReference(image=_png(64, 64), description="costume"),
                CharacterReference(image=_png(800, 400), description="character_mainoutfit", fidelity=0.75),
            ],
        )
    assert gen.model == Model.NAI_DIFFUSION_4_5_CURATED_INPAINTING
    p = _params(gen)
    assert _captions(p) == ["character"]
    assert p["director_reference_secondary_strength_values"] == [0.25]
    assert _size(p["director_reference_images"][0]) == (1536, 1024)


def test_img2img_takes_references():
    gen = GenerateImageInfer.build_img2img(
        "1girl",
        model=Model.NAI_DIFFUSION_5_FULL,
        image=_png(832, 1216),
        character_references=[CharacterReference(image=_png(64, 64), description="costume")],
    )
    assert _captions(_params(gen)) == ["costume"]


def test_sixteen_references_at_most_after_filtering():
    ref = CharacterReference(image=_png(8, 8))
    outfit = CharacterReference(image=_png(8, 8), description="costume")
    # the outfit reference is left out on V4.5 first, sixteen stay
    with pytest.warns(UserWarning, match="outfit"):
        p = _params(
            GenerateImageInfer.build_generate(
                "1girl", model=Model.NAI_DIFFUSION_4_5_FULL, character_references=[ref] * 16 + [outfit]
            )
        )
    assert len(p["director_reference_images"]) == 16
    with pytest.raises(ValueError, match="16"):
        GenerateImageInfer.build_generate("1girl", model=Model.NAI_DIFFUSION_5_FULL, character_references=[ref] * 17)


def test_vibes_are_left_out_with_a_reference():
    with pytest.warns(UserWarning, match="Vibe Transfer does not work together with Precise Reference") as caught:
        gen = GenerateImageInfer.build_generate(
            "1girl",
            model=Model.NAI_DIFFUSION_4_5_FULL,
            reference_image_multiple=["dmliZQ=="],
            reference_strength_multiple=[0.6],
            reference_information_extracted_multiple=[1.0],
            character_references=[CharacterReference(image=_png(8, 8))],
        )
    assert caught[0].filename == __file__  # past pydantic's validator frames too
    assert gen.parameters.reference_image_multiple is None
    assert gen.parameters.director_reference_images


def _with_stealth_metadata(width, height) -> bytes:
    pixels = np.zeros((height, width, 4), dtype=np.uint8)
    pixels[..., :3] = 128
    pixels[..., 3] = 254
    bits = np.unpackbits(np.frombuffer(b"stealth_pngcomp", dtype=np.uint8))
    column_major = pixels[..., 3].T.copy().reshape(-1)
    column_major[: len(bits)] |= bits
    pixels[..., 3] = column_major.reshape(width, height).T
    buf = io.BytesIO()
    Image.fromarray(pixels, "RGBA").save(buf, "PNG")
    return buf.getvalue()


def test_novelai_alpha_metadata_is_cleared():
    raw = _with_stealth_metadata(832, 1216)
    out = base64.b64decode(CharacterReference(image=raw).image_b64_for(Model.NAI_DIFFUSION_5_FULL))
    assert out != raw
    alpha = np.array(Image.open(io.BytesIO(out)))[..., 3]
    assert set(np.unique(alpha)) == {255}


def test_v45_canvas_is_black_under_transparent_pixels():
    raw = _png(1024, 1536, (255, 255, 255, 0), mode="RGBA")
    out = CharacterReference(image=raw).padded_image_b64()
    image = Image.open(io.BytesIO(base64.b64decode(out))).convert("RGB")
    assert image.getpixel((512, 768)) == (0, 0, 0)


def test_references_follow_the_model_the_request_goes_to():
    # nai-diffusion-5-curated-inpainting goes to V4.5 Curated inpainting: V4.5 rules, no outfit
    with pytest.warns(UserWarning, match="takes no outfit reference"):
        gen = GenerateImageInfer(
            input="1girl",
            model=Model.NAI_DIFFUSION_5_CURATED_INPAINTING,
            action="infill",
            parameters=GenerateImageInfer.build_infill(
                "1girl", model=Model.NAI_DIFFUSION_4_5_CURATED, image=_png(832, 1216), mask=_png(832, 1216)
            ).parameters,
            character_references=[
                CharacterReference(image=_png(800, 400), description="character_mainoutfit"),
                CharacterReference(image=_png(64, 64), description="costume"),
            ],
        )
    assert gen.model == Model.NAI_DIFFUSION_4_5_CURATED_INPAINTING
    p = _params(gen)
    assert _captions(p) == ["character"]
    assert _size(p["director_reference_images"][0]) == (1536, 1024)
    assert "character_references" not in gen.model_dump()


def test_fields_built_for_v5_are_refused_on_v45():
    v5 = GenerateImageInfer.build_generate(
        "1girl",
        model=Model.NAI_DIFFUSION_5_FULL,
        character_references=[CharacterReference(image=_png(64, 64), description="character_mainoutfit")],
    )
    with pytest.raises(ValueError, match="nai-diffusion-4-5-full takes no outfit reference"):
        GenerateImageInfer(input="1girl", model=Model.NAI_DIFFUSION_4_5_FULL, parameters=v5.parameters)
