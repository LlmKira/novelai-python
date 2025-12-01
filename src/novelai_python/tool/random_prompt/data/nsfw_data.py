# nsfw_data.py
from __future__ import annotations

import base64
import json
from typing import List, cast, TypedDict, Union

from pydantic import BaseModel, Field, ConfigDict


class TagEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    tag: str = Field(..., description="Тег или несколько через запятую")
    weight: Union[int, float] = Field(..., ge=1, le=100)
    extra: list[str] = Field(default_factory=list, exclude=True)


class NsfwData(TypedDict, total=False):
    p: List[list[Union[str, int, list[str]]]]
    mp: List[list[Union[str, int]]]
    n: List[list[Union[str, int]]]
    u: List[list[Union[str, int]]]
    nk: List[list[Union[str, int]]]
    bd: List[list[Union[str, int]]]
    nEx: List[list[Union[str, int]]]
    nSM: List[list[Union[str, int, list[str]]]]  # тут бывают кривые записи
    nSA: List[list[Union[str, int]]]
    nSP: List[list[Union[str, int]]]
    nPM: List[list[Union[str, int, list[str]]]]
    nPA: List[list[Union[str, int]]]
    nPP: List[list[Union[str, int]]]
    sMod: List[list[Union[str, int]]]
    sActMod: List[list[Union[str, int]]]
    sT: List[list[Union[str, int]]]
    h: str
    yu: str
    ya: str
    fu: str
    fwm: str
    fwf: str
    nw: str


# ====================== ЗАШИФРОВАННЫЕ ДАННЫЕ ======================
NSFW_DATA_ENCRYPTED = "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"


def _decode() -> dict:
    try:
        xor_bytes = base64.b64decode(NSFW_DATA_ENCRYPTED)
        # Мы ограничиваем результат байтом (0-255), чтобы Python не ругался
        decoded = bytes((b ^ i) & 0xFF for i, b in enumerate(xor_bytes))
        return json.loads(decoded.decode("utf-8"))
    except Exception as e:
        print(f"[NSFW] Decode failed: {e}")
        return {}


_raw = cast(NsfwData, _decode())


# ====================== ЭКСПОРТ ======================
NSFW_P       = _raw.get("p", [])
NSFW_MP      = _raw.get("mp", [])
NSFW_N       = _raw.get("n", [])
NSFW_U       = _raw.get("u", [])
NSFW_NK      = _raw.get("nk", [])
NSFW_BD      = _raw.get("bd", [])
NSFW_NEX     = _raw.get("nEx", [])
NSFW_NSM     = _raw.get("nSM", [])
NSFW_NSA     = _raw.get("nSA", [])
NSFW_NSP     = _raw.get("nSP", [])
NSFW_NPM     = _raw.get("nPM", [])
NSFW_NPA     = _raw.get("nPA", [])
NSFW_NPP     = _raw.get("nPP", [])
NSFW_SMOD    = _raw.get("sMod", [])
NSFW_SACTMOD = _raw.get("sActMod", [])
NSFW_ST      = _raw.get("sT", [])

NSFW_H  = _raw.get("h", "hetero")
NSFW_YU = _raw.get("yu", "yuri")
NSFW_YA = _raw.get("ya", "yaoi")
NSFW_FU = _raw.get("fu", "futanari")
NSFW_FWM = _raw.get("fwm", "futa with male")
NSFW_FWF = _raw.get("fwf", "futa with female")
NSFW_NW = _raw.get("nw", "nsfw")