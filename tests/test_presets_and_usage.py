"""Quality-tag strings per model (docs.novelai.net "Quality Tags")
and the Opus V5 usage bar on /user/subscription."""

from novelai_python._response.user.subscription import SubscriptionResp, SubscriptionUsage
from novelai_python.sdk.ai._enum import Model, get_modifiers, get_quality_presets


def test_quality_suffix_follows_docs_per_model():
    assert get_modifiers(Model.NAI_DIFFUSION_5_FULL).suffix == ", very aesthetic, masterpiece, no text"
    assert get_modifiers(Model.NAI_DIFFUSION_4_5_FULL).suffix == ", location, very aesthetic, masterpiece, no text"
    assert (
        get_modifiers(Model.NAI_DIFFUSION_4_5_CURATED).suffix
        == ", location, masterpiece, no text, -0.8::feet::, rating:general"
    )
    assert get_modifiers(Model.NAI_DIFFUSION_4_FULL).suffix == ", no text, best quality, very aesthetic, absurdres"
    assert (
        get_modifiers(Model.NAI_DIFFUSION_4_CURATED_PREVIEW).suffix
        == ", rating:general, amazing quality, very aesthetic, absurdres"
    )
    assert get_modifiers(Model.NAI_DIFFUSION_3).suffix == ", best quality, amazing quality, very aesthetic, absurdres"
    assert get_modifiers(Model.NAI_DIFFUSION_FURRY_3).suffix == ", {best quality}, {amazing quality}"


def test_v5_has_light_and_standard_presets():
    ids = {p.id: p.suffix for p in get_quality_presets(Model.NAI_DIFFUSION_5_FULL)}
    assert ids["standard"] == "very aesthetic, masterpiece, no text"
    assert ids["light"] == "very aesthetic, amazing quality, no text"
    assert ids["none"] == ""


def test_subscription_usage_is_optional_and_derived():
    base = {
        "tier": 3,
        "active": True,
        "expiresAt": 1,
        "accountType": 0,  # no paymentProcessorData: some accounts omit it
        "trainingStepsLeft": {"fixedTrainingStepsLeft": 10000, "purchasedTrainingSteps": 0},
        "perks": {
            "maxPriorityActions": 1,
            "startPriority": 1,
            "moduleTrainingSteps": 0,
            "unlimitedMaxPriority": True,
            "voiceGeneration": True,
            "imageGeneration": True,
            "unlimitedImageGeneration": True,
            "unlimitedImageGenerationLimits": [],
            "contextTokens": 8192,
        },
    }
    assert SubscriptionResp.model_validate(base).usage is None
    r = SubscriptionResp.model_validate(
        {**base, "usage": {"percent": 49, "isNegative": False, "timeUntilNextPercent": 7888}}
    )
    assert r.usage.percent == 49 and abs(r.usage.refill_percent_per_day - 10.95) < 0.01
    assert r.usage.images_left_estimate == int(49 * 17.3)
    neg = SubscriptionUsage(percent=-3, isNegative=True, timeUntilNextPercent=6048)
    assert neg.images_left_estimate == 0 and abs(neg.refill_percent_per_day - 14.29) < 0.01


def test_v45_request_matches_live_web_client_shape():
    """Keys/defaults observed in a real nai-diffusion-4-5-full request captured
    from the web client (payload_samples)."""
    from novelai_python.sdk.ai.generate_image import GenerateImageInfer

    g = GenerateImageInfer.build_generate(prompt="x", model=Model.NAI_DIFFUSION_4_5_FULL, width=1216, height=832)
    d = g.model_dump(mode="json", exclude_none=True)
    p = d["parameters"]
    live = {
        "add_original_image",
        "autoSmea",
        "cfg_rescale",
        "characterPrompts",
        "controlnet_strength",
        "deliberate_euler_ancestral_bug",
        "dynamic_thresholding",
        "height",
        "image_format",
        "inpaintImg2ImgStrength",
        "legacy",
        "legacy_uc",
        "legacy_v3_extend",
        "n_samples",
        "negative_prompt",
        "noise_schedule",
        "normalize_reference_strength_multiple",
        "params_version",
        "prefer_brownian",
        "qualityPresetId",
        "sampler",
        "scale",
        "seed",
        "steps",
        "tag_hint_qt",
        "tag_hint_uc_preset",
        "ucPresetId",
        "use_coords",
        "v4_negative_prompt",
        "v4_prompt",
        "width",
    }
    assert live <= set(p), live - set(p)
    assert (p["steps"], p["scale"], p["image_format"], p["tag_hint_qt"], p["tag_hint_uc_preset"]) == (
        28,
        5.0,
        "png",
        1,
        2,
    )
    assert p["ucPresetId"] == "heavy" and p["qualityPresetId"] == "standard" and p["params_version"] == 4
    assert "ucPreset" not in p and "qualityToggle" not in p


def test_v5_uses_qwen35_prompt_tokenizer(monkeypatch):
    from novelai_python._enum import TextTokenizerGroup
    from novelai_python.sdk.ai.generate_image import tokenizer as tk

    seen = []
    monkeypatch.setattr(tk, "get_tokenizer", lambda name: seen.append(name) or name)
    tk.get_prompt_tokenizer(Model.NAI_DIFFUSION_5_FULL)
    tk.get_prompt_tokenizer(Model.NAI_DIFFUSION_5_FULL_MEDIUM)
    tk.get_prompt_tokenizer(Model.NAI_DIFFUSION_4_5_FULL)
    tk.get_prompt_tokenizer(Model.NAI_DIFFUSION_3)
    assert seen == [
        TextTokenizerGroup.QWEN35,
        TextTokenizerGroup.QWEN35,
        TextTokenizerGroup.T5,
        TextTokenizerGroup.CLIP,
    ]
