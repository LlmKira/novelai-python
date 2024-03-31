from typing import Optional

from pydantic import BaseModel
from enum import Enum


class Speaker(BaseModel):
    """
    Speaker for /ai/generated_voice
    """
    sid: int = -1
    seed: Optional[str] = None
    name: str
    category: str

    @property
    def version(self):
        return "v2" if self.sid is None else "v1"


class VoiceSpeakerV1(Enum):
    """
    Speaker for /ai/generated_voice
    """
    Cyllene = Speaker(sid=17, name="Cyllene", category="female")
    Leucosia = Speaker(sid=95, name="Leucosia", category="female")
    Crina = Speaker(sid=44, name="Crina", category="female")
    Hespe = Speaker(sid=80, name="Hespe", category="female")
    Ida = Speaker(sid=106, name="Ida", category="female")
    Alseid = Speaker(sid=6, name="Alseid", category="male")
    Daphnis = Speaker(sid=10, name="Daphnis", category="male")
    Echo = Speaker(sid=16, name="Echo", category="male")
    Thel = Speaker(sid=41, name="Thel", category="male")
    Nomios = Speaker(sid=77, name="Nomios", category="male")
    # SeedInput = Speaker(sid=-1, name="Seed Input", category="custom")


class VoiceSpeakerV2(Enum):
    """
    Speaker for /ai/generated_voice
    """
    Ligeia = Speaker(name="Ligeia", category="unisex", seed="Anananan")
    Aini = Speaker(name="Aini", category="female", seed="Aini")
    Orea = Speaker(name="Orea", category="female", seed="Orea")
    Claea = Speaker(name="Claea", category="female", seed="Claea")
    Lim = Speaker(name="Lim", category="female", seed="Lim")
    Aurae = Speaker(name="Aurae", category="female", seed="Aurae")
    Naia = Speaker(name="Naia", category="female", seed="Naia")
    Aulon = Speaker(name="Aulon", category="male", seed="Aulon")
    Elei = Speaker(name="Elei", category="male", seed="Elei")
    Ogma = Speaker(name="Ogma", category="male", seed="Ogma")
    Raid = Speaker(name="Raid", category="male", seed="Raid")
    Pega = Speaker(name="Pega", category="male", seed="Pega")
    Lam = Speaker(name="Lam", category="male", seed="Lam")
