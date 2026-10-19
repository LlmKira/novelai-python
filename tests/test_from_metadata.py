from pathlib import Path

import pytest
from PIL import Image

from novelai_python.sdk.ai._enum import Action, Model
from novelai_python.sdk.ai.generate_image import GenerateImageInfer
from novelai_python.tool.image_metadata import CommentModel, ImageMetadata

FIXTURE = Path(__file__).parent / "fixtures" / "v5_signed.webp"


def test_rebuilds_v5_generation_from_signed_webp():
    meta = ImageMetadata.load_image(Image.open(FIXTURE))
    infer = GenerateImageInfer.from_metadata(meta)
    p = infer.parameters
    c = meta.Comment
    assert infer.model == Model.NAI_DIFFUSION_5_FULL and infer.action == Action.GENERATE
    # prompt and uc are final in the metadata: nothing is added on top
    assert infer.input == c.v4_prompt["caption"]["base_caption"]
    assert p.negative_prompt == c.uc
    assert p.v4_prompt.caption.base_caption == c.prompt
    assert p.v4_negative_prompt.caption.base_caption == c.uc
    assert (p.seed, p.steps, p.scale, p.width, p.height) == (c.seed, c.steps, c.scale, c.width, c.height)
    assert p.sampler.value == c.sampler and p.noise_schedule.value == c.noise_schedule
    assert p.skip_cfg_above_sigma is None


def _meta(**comment) -> ImageMetadata:
    base = {
        "prompt": "2girls, park, very aesthetic, masterpiece, no text",
        "uc": "lowres, bad quality",
        "steps": 23,
        "height": 1216,
        "width": 832,
        "scale": 5.0,
        "cfg_rescale": 0.5,
        "seed": 42,
        "sampler": "k_euler_ancestral",
        "noise_schedule": "karras",
        "skip_cfg_above_sigma": 23,
        "request_type": "PromptGenerateRequest",
        "v4_prompt": {
            "caption": {
                "base_caption": "2girls, park, very aesthetic, masterpiece, no text",
                "char_captions": [
                    {"char_caption": "girl, black hair", "centers": [{"x": 0.3, "y": 0.5}]},
                    {"char_caption": "girl, red hair", "centers": [{"x": 0.7, "y": 0.5}]},
                ],
            },
            "use_coords": True,
            "use_order": True,
        },
        "v4_negative_prompt": {
            "caption": {
                "base_caption": "lowres, bad quality",
                "char_captions": [
                    {"char_caption": "blonde hair", "centers": [{"x": 0.3, "y": 0.5}]},
                    {"char_caption": "", "centers": [{"x": 0.7, "y": 0.5}]},
                ],
            },
            "legacy_uc": False,
        },
    }
    base.update(comment)
    return ImageMetadata(Comment=CommentModel(**base), Source="NovelAI Diffusion V5 0ADF9AB7")


def test_characters_keep_negative_and_position():
    p = GenerateImageInfer.from_metadata(_meta()).parameters
    assert [c.prompt for c in p.characterPrompts] == ["girl, black hair", "girl, red hair"]
    assert [c.uc for c in p.characterPrompts] == ["blonde hair", ""]
    assert p.v4_prompt.use_coords is True
    centers = [cc.centers[0] for cc in p.v4_prompt.caption.char_captions]
    assert [(c.x, c.y) for c in centers] == [(0.3, 0.5), (0.7, 0.5)]
    assert [cc.char_caption for cc in p.v4_negative_prompt.caption.char_captions] == ["blonde hair", ""]
    assert p.cfg_rescale == 0.5
    assert p.skip_cfg_above_sigma is None  # V5 has no variety boost


def test_variety_sigma_is_not_scaled_twice():
    # already scaled to the image size by the server: taken as is
    meta = _meta(width=1024, height=1024)
    infer = GenerateImageInfer.from_metadata(meta, model=Model.NAI_DIFFUSION_4_5_FULL)
    assert infer.parameters.skip_cfg_above_sigma == 23


def test_img2img_needs_the_source_image():
    meta = _meta(request_type="Img2ImgRequest", strength=0.8, noise=0.1, extra_noise_seed=41, color_correct=False)
    assert GenerateImageInfer.from_metadata(meta).action == Action.GENERATE
    infer = GenerateImageInfer.from_metadata(meta, image=FIXTURE.read_bytes())
    p = infer.parameters
    assert infer.action == Action.IMG2IMG
    assert (p.strength, p.noise, p.extra_noise_seed, p.color_correct) == (0.8, 0.1, 41, False)


@pytest.mark.parametrize(
    ("source", "model"),
    [
        ("NovelAI Diffusion V5 0ADF9AB7", Model.NAI_DIFFUSION_5_FULL),
        ("NovelAI Diffusion V5 93F4BD30", Model.NAI_DIFFUSION_5_FULL_MEDIUM),
        ("NovelAI Diffusion V5 DB276663", Model.NAI_DIFFUSION_5_CURATED),
        ("NovelAI Diffusion V5 00000000", Model.NAI_DIFFUSION_5_CURATED),  # the web client's default
    ],
)
def test_v5_model_from_source_hash(source, model):
    from novelai_python.sdk.ai._enum import find_model_by_hashcode

    assert find_model_by_hashcode(source) == model


def test_unknown_model_and_missing_comment():
    with pytest.raises(ValueError):
        GenerateImageInfer.from_metadata(ImageMetadata(Comment=CommentModel(prompt="x"), Source="Stable Diffusion"))
    infer = GenerateImageInfer.from_metadata(
        ImageMetadata(Comment=CommentModel(prompt="x", seed=1), Source="Stable Diffusion"),
        model=Model.NAI_DIFFUSION_4_5_FULL,
    )
    assert infer.model == Model.NAI_DIFFUSION_4_5_FULL
    with pytest.raises(ValueError):
        GenerateImageInfer.from_metadata(ImageMetadata(Source="NovelAI Diffusion V5 0ADF9AB7"))
