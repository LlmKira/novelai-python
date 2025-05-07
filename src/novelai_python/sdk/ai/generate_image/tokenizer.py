from novelai_python._enum import TextTokenizerGroup
from novelai_python.sdk.ai.generate_image import Model
from novelai_python.tokenizer import NaiTokenizer


def get_prompt_tokenizer(model: Model):
    """
    Only for IMAGE prompt length calculation
    :param model:
    :return:
    """
    if model in [
        Model.CUSTOM,
        Model.NAI_DIFFUSION_4_5_CURATED,
        Model.NAI_DIFFUSION_4_5_CURATED_INPAINTING,
        Model.NAI_DIFFUSION_4_CURATED_PREVIEW,
        Model.NAI_DIFFUSION_4_CURATED_INPAINTING,
        Model.NAI_DIFFUSION_4_FULL,
        Model.NAI_DIFFUSION_4_FULL_INPAINTING,
    ]:
        return NaiTokenizer(TextTokenizerGroup.T5)
    return NaiTokenizer(TextTokenizerGroup.CLIP)
