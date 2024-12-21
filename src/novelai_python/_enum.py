from enum import Enum
from typing import Optional, Union


class TextLLMModel(Enum):
    NEO_2B = "2.7B"
    J_6B = "6B"
    J_6B_V3 = "6B-v3"
    J_6B_V4 = "6B-v4"
    GENJI_PYTHON_6B = "genji-python-6b"
    GENJI_JP_6B = "genji-jp-6b"
    GENJI_JP_6B_V2 = "genji-jp-6b-v2"
    EUTERPE_V0 = "euterpe-v0"
    EUTERPE_V2 = "euterpe-v2"
    KRAKE_V1 = "krake-v1"
    KRAKE_V2 = "krake-v2"
    BLUE = "blue"
    RED = "red"
    GREEN = "green"
    PURPLE = "purple"
    PINK = "pink"
    YELLOW = "yellow"
    WHITE = "white"
    BLACK = "black"
    CASSANDRA = "cassandra"
    COMMENT_BOT = "hypebot"
    INFILL = "infillmodel"
    CLIO = "clio-v1"
    KAYRA = "kayra-v1"
    ERATO = "llama-3-erato-v1"


class TextTokenizerGroup(object):
    GENJI = "genji_tokenizer.def"
    PILE = "pile_tokenizer.def"
    PILE_NAI = "pile_tokenizer.def"
    NAI_INLINE = "gpt2_tokenizer.def"
    NERDSTASH_V2 = "nerdstash_tokenizer_v2.def"
    NERDSTASH = "nerdstash_tokenizer.def"
    LLAMA3 = "llama3_tokenizer.def"
    GPT2 = "gpt2_tokenizer.def"
    CLIP = "clip_tokenizer.def"
    T5 = "t5_tokenizer.def"


TextLLMModelTypeAlias = Union[TextLLMModel, str]

TOKENIZER_MODEL_MAP = {
    TextLLMModel.GENJI_JP_6B_V2: TextTokenizerGroup.GENJI,
    TextLLMModel.CASSANDRA: TextTokenizerGroup.PILE,
    TextLLMModel.KRAKE_V2: TextTokenizerGroup.PILE,
    TextLLMModel.INFILL: TextTokenizerGroup.NAI_INLINE,
    TextLLMModel.KAYRA: TextTokenizerGroup.NERDSTASH_V2,
    TextLLMModel.BLUE: TextTokenizerGroup.NERDSTASH_V2,
    TextLLMModel.PINK: TextTokenizerGroup.NERDSTASH_V2,
    TextLLMModel.YELLOW: TextTokenizerGroup.NERDSTASH_V2,
    TextLLMModel.RED: TextTokenizerGroup.NERDSTASH_V2,
    TextLLMModel.GREEN: TextTokenizerGroup.NERDSTASH_V2,
    TextLLMModel.BLACK: TextTokenizerGroup.NERDSTASH_V2,
    TextLLMModel.CLIO: TextTokenizerGroup.NERDSTASH,
    TextLLMModel.PURPLE: TextTokenizerGroup.LLAMA3,
    TextLLMModel.WHITE: TextTokenizerGroup.LLAMA3,
    TextLLMModel.ERATO: TextTokenizerGroup.LLAMA3,
}

COLORS_LLM = [
    TextLLMModel.BLUE,
    TextLLMModel.RED,
    TextLLMModel.GREEN,
    TextLLMModel.PURPLE,
    TextLLMModel.PINK,
    TextLLMModel.YELLOW,
    TextLLMModel.WHITE,
    TextLLMModel.BLACK,
]


def get_llm_group(model: TextLLMModel) -> Optional[TextTokenizerGroup]:
    if isinstance(model, str):
        model = TextLLMModel(model)
    return TOKENIZER_MODEL_MAP.get(model, None)


def get_tokenizer_model(model: TextLLMModel) -> str:
    if isinstance(model, str):
        model = TextLLMModel(model)
    group = TOKENIZER_MODEL_MAP.get(model, TextTokenizerGroup.GPT2)
    return group


def get_tokenizer_model_url(model: TextLLMModel) -> str:
    model_name = get_tokenizer_model(model)
    if not model_name.endswith(".def"):
        model_name = f"{model_name}.def"
    return f"https://novelai.net/tokenizer/compressed/{model_name}?v=2&static=true"
