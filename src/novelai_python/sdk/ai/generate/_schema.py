from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple, Union

from pydantic import BaseModel, Field, ConfigDict

"""
class StorySettings(BaseModel):
    parameters: Optional[dict] = {}
    preset: Optional[str] = ''
    trimResponses: Optional[bool] = True
    banBrackets: Optional[bool] = True
    prefix: Optional[str] = 'vanilla'
    dynamicPenaltyRange: Optional[bool] = False
    prefixMode: Optional[int] = 0
    mode: Optional[int] = 0
    model: Optional[TextLLMModel] = TextLLMModel.J_6B_V4
"""
"""
def is_theme_need_model(model: TextLLMModel, entity: StorySettings):
    # 定义一个集合包含允许的模型
    valid_models = [TextLLMModel.CLIO, TextLLMModel.KAYRA, TextLLMModel.ERATO] + COLORS_LLM
    if model is None:
        model = TextLLMModel.KAYRA
    # 检查模型是否在允许列表中
    if model in valid_models:
        return entity.mode == 1
    else:
        mode_from_prefix = entity.prefix
        prefix_mode = 0
        for theme in get_themes():
            if theme.label == mode_from_prefix:
                prefix_mode = theme.mode
                break
        return prefix_mode == 1 or entity.prefixMode == 1
"""


class Theme(BaseModel):
    label: str
    mode: int
    description: str


class PenStyle(Enum):
    Off = "off"
    VeryLight = "very_light"
    Light = "light"
    Default = "medium"
    Aggressive = "aggressive"
    VeryAggressive = "very_aggressive"


@dataclass
class Key(object):
    Temperature = ("temperature", 0)
    TopK = ("top_k", 1)
    TopP = ("top_p", 2)
    TFS = ("tfs", 3)
    TopA = ("top_a", 4)
    TypicalP = ("typical_p", 5)
    Cfg = ("cfg", 6)
    TopG = ("top_g", 7)
    Mirostat = ("mirostat", 8)
    Math1 = ("math1", 9)
    MinP = ("min_p", 10)


class KeyOrderEntry(BaseModel):
    id: Tuple[str, int]
    enabled: bool


class LogitBiasGroup(BaseModel):
    sequence: List[int]
    bias: float = Field(default=None, gt=-1, lt=1)
    ensure_sequence_finish: bool
    generate_once: bool


class AdvanceLLMSetting(BaseModel):
    """
    LLM Generation Request Parameters
    """
    min_length: Optional[int] = 1
    max_length: Optional[int] = None
    repetition_penalty: Optional[Union[float, int]] = Field(default=None, allow_inf_nan=False)
    generate_until_sentence: Optional[bool] = True
    use_cache: Optional[bool] = False
    use_string: Optional[bool] = False
    return_full_text: Optional[bool] = False
    prefix: Optional[str] = ""
    logit_bias_exp: Optional[List[LogitBiasGroup]] = None
    num_logprobs: Optional[int] = None
    order: List[int] = Field(default_factory=list)
    bracket_ban: Optional[bool] = True
    model_config = ConfigDict(extra="allow")


class LLMGenerationParams(BaseModel):
    """
    LLM Generation Settings
    """
    textGenerationSettingsVersion: Optional[int] = None
    temperature: Optional[Union[float, int]] = Field(default=None, allow_inf_nan=False)
    max_length: Optional[int] = Field(default=None, ge=1, le=100)  # Max 150(vip3),100(vip2)
    min_length: Optional[int] = Field(default=None, ge=1, le=100)  # Max 150(vip3),100(vip2)
    top_k: Optional[int] = Field(default=None, ge=0)
    top_p: Optional[Union[float, int]] = Field(default=None, gt=0, le=1, allow_inf_nan=False)
    top_a: Optional[Union[float, int]] = Field(default=None, ge=0, allow_inf_nan=False)
    typical_p: Optional[Union[float, int]] = Field(default=None, ge=0, le=1, allow_inf_nan=False)
    tail_free_sampling: Optional[Union[float, int]] = Field(default=None, ge=0, allow_inf_nan=False)
    repetition_penalty: Optional[Union[float, int]] = Field(default=None, gt=0, allow_inf_nan=False)
    repetition_penalty_range: Optional[int] = Field(default=None, ge=0)
    repetition_penalty_slope: Optional[Union[float, int]] = Field(default=None, ge=0, allow_inf_nan=False)

    eos_token_id: int = None
    bad_words_ids: Optional[List[List[int]]] = None
    logit_bias_groups: Optional[List[LogitBiasGroup]] = Field(default_factory=list)

    repetition_penalty_frequency: Optional[Union[float, int]] = Field(default=None, allow_inf_nan=False)
    repetition_penalty_presence: Optional[Union[float, int]] = Field(default=None, allow_inf_nan=False)
    repetition_penalty_whitelist: Optional[List[int]] = None
    repetition_penalty_default_whitelist: Optional[bool] = None
    cfg_scale: Optional[Union[float, int]] = Field(default=None, allow_inf_nan=False)
    cfg_uc: Optional[str] = None
    phrase_rep_pen: PenStyle = PenStyle.Off
    top_g: Optional[Union[float, int]] = Field(default=None, allow_inf_nan=False)
    mirostat_tau: Optional[Union[float, int]] = Field(default=None, allow_inf_nan=False)
    mirostat_lr: Optional[Union[float, int]] = Field(default=None, allow_inf_nan=False)
    math1_temp: Optional[Union[float, int]] = Field(default=None, allow_inf_nan=False)
    math1_quad: Optional[Union[float, int]] = Field(default=None, allow_inf_nan=False)
    math1_quad_entropy_scale: Optional[Union[float, int]] = Field(default=None, allow_inf_nan=False)
    min_p: Optional[Union[float, int]] = Field(default=None, allow_inf_nan=False)

    order: Union[List[int], List[KeyOrderEntry]] = Field(
        default=[
            KeyOrderEntry(id=Key.Cfg, enabled=False),
            KeyOrderEntry(id=Key.Temperature, enabled=True),
            KeyOrderEntry(id=Key.TopK, enabled=True),
            KeyOrderEntry(id=Key.TopP, enabled=True),
            KeyOrderEntry(id=Key.TFS, enabled=True),
            KeyOrderEntry(id=Key.TopA, enabled=False),
            KeyOrderEntry(id=Key.TypicalP, enabled=False),
            KeyOrderEntry(id=Key.TopG, enabled=False),
            KeyOrderEntry(id=Key.Mirostat, enabled=False),
            KeyOrderEntry(id=Key.Math1, enabled=False),
            KeyOrderEntry(id=Key.MinP, enabled=False),
        ]
    )

    def get_base_map(self):
        parameters = self.model_dump(mode="json", exclude_none=True)
        skipped_params = {
            "textGenerationSettingsVersion",
            "eos_token_id",
            "bad_words_ids",
            "logit_bias_groups",
            "order"
        }
        return {key: value for key, value in parameters.items() if key not in skipped_params}


class ContextConfig(BaseModel):
    prefix: str
    suffix: str
    tokenBudget: int
    reservedTokens: int
    budgetPriority: int
    trimDirection: str
    insertionType: str
    maximumTrimType: str
    insertionPosition: int


class EphemeralDefaults(BaseModel):
    text: str
    contextConfig: ContextConfig
    startingStep: int
    delay: int
    duration: int
    repeat: bool
    reverse: bool


class LoreDefaults(BaseModel):
    text: str
    contextConfig: ContextConfig
    lastUpdatedAt: str
    displayName: str
    keys: List[str]
    searchRange: int
    enabled: bool
    forceActivation: bool
    keyRelative: bool
    nonStoryActivatable: bool


class StoryDefault(BaseModel):
    prefix: str
    suffix: str
    tokenBudget: int
    reservedTokens: int
    budgetPriority: int
    trimDirection: str
    insertionType: str
    maximumTrimType: str
    insertionPosition: int


class ContextDefaults(BaseModel):
    text: str
    contextConfig: ContextConfig


class ContextPresets(BaseModel):
    contextDefaults: Optional[List[ContextDefaults]]
    ephemeralDefaults: Optional[List[EphemeralDefaults]]
    loreDefaults: Optional[List[LoreDefaults]]
    storyDefault: Optional[StoryDefault]


class Preset(BaseModel):
    presetVersion: int
    remoteId: str
    name: str
    id: str
    parameters: LLMGenerationParams
    description: str
    contextPresets: Optional[ContextPresets] = None
