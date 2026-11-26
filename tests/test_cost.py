"""Prices as the novelai.net web client shows them (checkStableDiffusionPrice and the image tools hook)."""

import pytest

from novelai_python.sdk.ai._cost import CostCalculator
from novelai_python.sdk.ai._enum import Model, Sampler
from novelai_python.sdk.ai.augment_image import AugmentImageInfer
from novelai_python.sdk.ai.augment_image._enum import ReqType


def _price(model, opus=False, negative=False, w=832, h=1216, steps=28, n=1, refs=0, vibes=0):
    return CostCalculator.calculate(
        width=w,
        height=h,
        steps=steps,
        image=False,
        n_samples=n,
        account_tier=3 if opus else 1,
        strength=None,
        is_sm_enabled=False,
        is_sm_dynamic=False,
        is_account_active=True,
        sampler=Sampler.K_EULER_ANCESTRAL,
        model=model,
        usage_negative=negative,
        character_references=refs,
        vibe_references=vibes,
    )


def test_v5_costs_one_and_a_half_times_v45():
    assert _price(Model.NAI_DIFFUSION_4_5_FULL) == 20
    assert _price(Model.NAI_DIFFUSION_5_FULL) == 30


def test_medium_is_high_at_23_steps_over_1_75():
    # "about 42% less than a High 23 step generation" (docs.novelai.net, Effort Toggle): 26 against 15
    assert _price(Model.NAI_DIFFUSION_5_FULL, steps=23) == 26
    for steps in (14, 23, 28):
        assert _price(Model.NAI_DIFFUSION_5_FULL_MEDIUM, steps=steps) == 15
    assert _price(Model.NAI_DIFFUSION_5_FULL_MEDIUM, w=1024, h=1024) == 15


def test_opus_free_generation_and_usage_bar():
    assert _price(Model.NAI_DIFFUSION_5_FULL, opus=True) == 0
    # the bar below zero ends the free generation on V5 Full, Medium and Curated
    assert _price(Model.NAI_DIFFUSION_5_FULL, opus=True, negative=True) == 30
    assert _price(Model.NAI_DIFFUSION_5_FULL_MEDIUM, opus=True, negative=True) == 15
    for inpainting in (Model.NAI_DIFFUSION_5_FULL_INPAINTING, Model.NAI_DIFFUSION_5_FULL_MEDIUM_INPAINTING):
        assert _price(inpainting, opus=True, negative=True) > 0
    assert _price(Model.NAI_DIFFUSION_5_FULL, opus=True, n=4) == 90  # one of four is free
    assert _price(Model.NAI_DIFFUSION_5_FULL, opus=True, w=1216, h=1216) == 44


def test_reference_surcharges():
    assert _price(Model.NAI_DIFFUSION_4_5_FULL, opus=True, refs=1) == 5  # measured live on Opus
    assert _price(Model.NAI_DIFFUSION_4_5_FULL, opus=True, refs=2, n=2) == 20 + 20
    # V5: the same 5 per reference and image, the free Opus image included
    assert _price(Model.NAI_DIFFUSION_5_FULL, opus=True, refs=1) == 5
    assert _price(Model.NAI_DIFFUSION_5_FULL, opus=True, refs=1, n=2) == 30 + 10
    assert _price(Model.NAI_DIFFUSION_5_CURATED, refs=3) == 30 + 15


def test_vibe_surcharge_is_per_image_and_only_on_encoded_vibes():
    assert _price(Model.NAI_DIFFUSION_4_5_FULL, opus=True, vibes=6) == 4
    assert _price(Model.NAI_DIFFUSION_4_5_FULL, opus=True, vibes=6, n=2) == 20 + 8
    assert _price(Model.NAI_DIFFUSION_4_5_FULL, vibes=6, refs=1) == 20 + 5  # no vibes with a reference
    assert _price(Model.NAI_DIFFUSION_3, vibes=6) == _price(Model.NAI_DIFFUSION_3)  # V3 vibes are not encoded


def test_no_reference_surcharge_where_the_model_leaves_references_out():
    inpaint = {"mask": True, "image": True, "character_references": 1}
    common = {
        "width": 832,
        "height": 1216,
        "steps": 23,
        "n_samples": 1,
        "account_tier": 1,
        "strength": None,
        "is_sm_enabled": False,
        "is_sm_dynamic": False,
        "is_account_active": True,
        "sampler": Sampler.K_EULER_ANCESTRAL,
    }
    v5 = CostCalculator.calculate(model=Model.NAI_DIFFUSION_5_FULL_INPAINTING, **common, **inpaint)
    v45 = CostCalculator.calculate(model=Model.NAI_DIFFUSION_4_5_CURATED_INPAINTING, **common, **inpaint)
    assert v5 == CostCalculator.calculate(model=Model.NAI_DIFFUSION_5_FULL_INPAINTING, **common, mask=True, image=True)
    assert (
        v45
        == CostCalculator.calculate(model=Model.NAI_DIFFUSION_4_5_CURATED_INPAINTING, **common, mask=True, image=True)
        + 5
    )


@pytest.mark.parametrize(
    ("tool", "size", "regular", "opus"),
    [
        ("lineart", (832, 1216), 20, 0),
        ("lineart", (2048, 2048), 60, 60),  # scaled down to 3 MP, over the free area
        ("bg-removal", (832, 1216), 65, 65),  # 3 x 20 + 5, never free
        ("pixel-snap", (832, 1216), 0, 0),
        ("upscale", (832, 1216), 1, 1),  # measured live
        ("upscale", (2048, 2048), -2, -2),  # the web client upscales up to 1 MP
    ],
)
def test_tool_prices(tool, size, regular, opus):
    assert CostCalculator.calculate_tool(tool, *size) == regular
    assert CostCalculator.calculate_tool(tool, *size, account_tier=3) == opus


def test_augment_request_uses_tool_price():
    request = AugmentImageInfer(req_type=ReqType.BG_REMOVAL, width=832, height=1216, image="aGk=")
    assert request.calculate_cost(is_opus=True) == 65
    request = AugmentImageInfer(req_type=ReqType.SKETCH, width=832, height=1216, image="aGk=")
    assert request.calculate_cost(is_opus=True) == 0


def test_variety_boost_uses_the_model_sigma_in_img2img():
    import base64
    import io

    from PIL import Image

    from novelai_python.sdk.ai.generate_image import GenerateImageInfer

    buf = io.BytesIO()
    Image.new("RGB", (832, 1216)).save(buf, "PNG")
    image = base64.b64encode(buf.getvalue()).decode()
    common = {"image": image, "width": 832, "height": 1216, "variety_boost": True}
    v45 = GenerateImageInfer.build_img2img("1girl", model=Model.NAI_DIFFUSION_4_5_FULL, **common)
    v4 = GenerateImageInfer.build_img2img("1girl", model=Model.NAI_DIFFUSION_4_FULL, **common)
    assert v45.parameters.skip_cfg_above_sigma == 58
    assert v4.parameters.skip_cfg_above_sigma == 19


def test_v5_curated_is_inpainted_with_v45_curated():
    from novelai_python.sdk.ai._enum import get_inpainting_model

    assert get_inpainting_model(Model.NAI_DIFFUSION_5_CURATED) == Model.NAI_DIFFUSION_4_5_CURATED_INPAINTING
    assert get_inpainting_model("nai-diffusion-5-full") == Model.NAI_DIFFUSION_5_FULL_INPAINTING
    assert get_inpainting_model(Model.NAI_DIFFUSION_4_5_FULL_INPAINTING) == Model.NAI_DIFFUSION_4_5_FULL_INPAINTING
