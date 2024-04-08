# MIT: https://github.com/Aedial/novelai-api/blob/main/novelai_api/
from typing import Optional, Union, List

import pydantic
from pydantic import model_validator, Field, BaseModel

from ._enum import PenStyle


class LogitBiasExp(BaseModel):
    sequence: List[int]
    bias: float = Field(default=None, gt=-1, lt=1)
    ensure_sequence_finish: bool
    generate_once: bool


class Params(BaseModel):
    bad_words_ids: List[List[int]] = []
    logit_bias_exp: Optional[List[LogitBiasExp]] = []
    max_length: int = Field(default=40, ge=1, le=100)  # Max 150(vip3),100(vip2)
    """Default 30"""
    min_length: int = Field(default=1, ge=1, le=100)  # Max 150(vip3),100(vip2)
    """Default 10"""
    eos_token_id: int = Field(default=None, ge=0)  # 50528
    typical_p: float = Field(default=None, gt=0, le=1)
    num_logprobs: Optional[int] = None
    order: Optional[List[int]] = None
    phrase_rep_pen: PenStyle = PenStyle.Off
    prefix: str = "vanilla"
    repetition_penalty: float = Field(default=1, gt=0)
    repetition_penalty_frequency: float = Field(default=0, ge=0)
    repetition_penalty_presence: float = Field(default=0, ge=0)
    repetition_penalty_range: int = Field(default=None, ge=0)  # 560 2048
    repetition_penalty_slope: float = Field(default=None, ge=0)
    repetition_penalty_whitelist: List[int] = []
    return_full_text: bool = False
    stop_sequences: Optional[Union[List[List[int]], List[str]]] = []
    generate_until_sentence: bool = True

    tail_free_sampling: float = Field(default=1.0, gt=0, le=1)
    temperature: float = Field(default=1, gt=0)
    """Default 1"""
    top_a: Optional[float] = Field(default=0.1, gt=0, le=1)
    top_k: int = Field(default=None, ge=0)
    top_p: float = Field(default=None, gt=0, le=1)
    use_cache: bool = False
    use_string: bool = False
    """Default False"""
    cfg_uc: str = None
    cfg_scale: float = None
    top_g: float = None
    mirostat_tau: float = None
    mirostat_lr: float = None

    @model_validator(mode="after")
    def validate_model(self):
        if self.min_length > self.max_length:
            raise pydantic.ValidationError("min_length must be less than or equal to max_length")
        return self


_HyperBot = {
    "stop_sequences": [[48585]],
    "temperature": 1,
    "max_length": 80,
    "min_length": 1,
    "top_k": 0,
    "top_p": 1,
    "tail_free_sampling": 0.95,
    "repetition_penalty": 1,
    "repetition_penalty_range": 2048,
    "repetition_penalty_slope": 0.18,
    "repetition_penalty_frequency": 0,
    "repetition_penalty_presence": 0,
}
_Storywriter = {
    "temperature": 0.72,
    "max_length": 40,
    "min_length": 1,
    "top_k": 0,
    "top_p": 0.725,
    "top_a": 1,
    "typical_p": 1,
    "tail_free_sampling": 1,
    "repetition_penalty": 2.75,
    "repetition_penalty_range": 2048,
    "repetition_penalty_slope": 0.18,
    "repetition_penalty_frequency": 0,
    "repetition_penalty_presence": 0,
}
_Sigurd = {
    "temperature": 0.72,
    "max_length": 40,
    "min_length": 1,
    "top_k": 0,
    "top_p": 0.725,
    "top_a": 1,
    "typical_p": 1,
    "tail_free_sampling": 1,
    "repetition_penalty": 2.75,
    "repetition_penalty_range": 2048,
    "repetition_penalty_slope": 0.18,
    "repetition_penalty_frequency": 0,
    "repetition_penalty_presence": 0,
}
_Euterpe = {
    "temperature": 0.86,
    "max_length": 40,
    "min_length": 1,
    "top_k": 0,
    "top_p": 0.925,
    "top_a": 1,
    "typical_p": 1,
    "tail_free_sampling": 0.925,
    "repetition_penalty": 2.25,
    "repetition_penalty_range": 2048,
    "repetition_penalty_slope": 0.09,
    "repetition_penalty_frequency": 0,
    "repetition_penalty_presence": 0,
}
_Genji = {
    "temperature": 0.86,
    "max_length": 40,
    "min_length": 1,
    "top_k": 0,
    "top_p": 1,
    "top_a": 1,
    "typical_p": 1,
    "tail_free_sampling": 0.927,
    "repetition_penalty": 2.9,
    "repetition_penalty_range": 2048,
    "repetition_penalty_slope": 3.33,
    "repetition_penalty_frequency": 0,
    "repetition_penalty_presence": 0,
}
_Snek = {
    "temperature": 0.72,
    "max_length": 40,
    "min_length": 1,
    "top_k": 0,
    "top_p": 0.725,
    "top_a": 1,
    "typical_p": 1,
    "tail_free_sampling": 1,
    "repetition_penalty": 2.75,
    "repetition_penalty_range": 2048,
    "repetition_penalty_slope": 0.18,
    "repetition_penalty_frequency": 0,
    "repetition_penalty_presence": 0,
}
_Inline = {
    "eos_token_id": 50258,
    "temperature": 0.8,
    "max_length": 100,
    "min_length": 1,
    "top_k": 0,
    "top_p": 1,
    "tail_free_sampling": 0.859,
    "repetition_penalty": 1.084375,
    "repetition_penalty_range": 2048,
    "repetition_penalty_slope": 0.18,
    "repetition_penalty_frequency": 0,
    "repetition_penalty_presence": 0,
}
_Kayra = {
    "temperature": 1.35,
    "max_length": 40,
    "min_length": 1,
    "top_k": 15,
    "top_p": 0.85,
    "top_a": 0.1,
    "typical_p": 1,
    "tail_free_sampling": 0.915,
    "repetition_penalty": 2.8,
    "repetition_penalty_range": 2048,
    "repetition_penalty_slope": 0.02,
    "repetition_penalty_frequency": 0.02,
    "repetition_penalty_presence": 0,
    "repetition_penalty_default_whitelist": True,
    "cfg_scale": 1,
    "cfg_uc": "",
    "phrase_rep_pen": "aggressive",
    "top_g": 0
}
_Krake = {
    "temperature": 1.33,
    "max_length": 40,
    "min_length": 1,
    "top_k": 81,
    "top_p": 0.88,
    "top_a": 0.085,
    "typical_p": 0.965,
    "tail_free_sampling": 0.937,
    "repetition_penalty": 1.05,
    "repetition_penalty_range": 560,
    "repetition_penalty_slope": 0,
    "repetition_penalty_frequency": 0,
    "repetition_penalty_presence": 0,
}
_Clio = {
    "temperature": 1.21,
    "max_length": 75,
    "min_length": 1,
    "top_k": 0,
    "top_p": 0.912,
    "top_a": 1,
    "typical_p": 0.912,
    "tail_free_sampling": 0.921,
    "repetition_penalty": 1.21,
    "repetition_penalty_range": 321,
    "repetition_penalty_slope": 2.1,
    "repetition_penalty_frequency": 0.00621,
    "repetition_penalty_presence": 0,
}
PRESET = {
    "Sigurd": Params.model_validate(_Sigurd),
    "Euterpe": Params.model_validate(_Euterpe),
    "Krake": Params.model_validate(_Krake),
    "Clio": Params.model_validate(_Clio),
    "Kayra": Params.model_validate(_Kayra),
    "Genji": Params.model_validate(_Genji),
    "Snek": Params.model_validate(_Snek),
    "HypeBot": Params.model_validate(_HyperBot),
    "Inline": Params.model_validate(_Inline),
}
