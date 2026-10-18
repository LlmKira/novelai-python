from novelai_python._enum import TextTokenizerGroup
from novelai_python.sdk.ai._enum import is_v5_model
from novelai_python.sdk.ai.generate_image import Model
from novelai_python.tokenizer import NaiTokenizer

_T5_MODELS = {
    Model.NAI_DIFFUSION_4_5_FULL,
    Model.NAI_DIFFUSION_4_5_FULL_INPAINTING,
    Model.NAI_DIFFUSION_4_5_CURATED,
    Model.NAI_DIFFUSION_4_5_CURATED_INPAINTING,
    Model.NAI_DIFFUSION_4_CURATED_PREVIEW,
    Model.NAI_DIFFUSION_4_CURATED_INPAINTING,
    Model.NAI_DIFFUSION_4_FULL,
    Model.NAI_DIFFUSION_4_FULL_INPAINTING,
}


def get_prompt_tokenizer(model: Model) -> NaiTokenizer:
    """
    Only for IMAGE prompt length calculation.
    V5 family -> qwen35 (what novelai.net/image loads), V4/V4.5 -> T5, older -> CLIP.
    """
    if model == Model.CUSTOM or is_v5_model(model):
        return NaiTokenizer(TextTokenizerGroup.QWEN35)
    if model in _T5_MODELS:
        return NaiTokenizer(TextTokenizerGroup.T5)
    return NaiTokenizer(TextTokenizerGroup.CLIP)
