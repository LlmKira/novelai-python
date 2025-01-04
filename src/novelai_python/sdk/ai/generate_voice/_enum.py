from enum import Enum

from pydantic import BaseModel


class Speaker(BaseModel):
    """
    Speaker for /ai/generated_voice
    """
    voice: int = -1
    seed: str = "kurumuz12"
    name: str
    category: str

    @property
    def version(self):
        return "v2" if self.voice == -1 else "v1"


class VoiceSpeakerV1(Enum):
    """
    Speaker for /ai/generated_voice
    """
    Cyllene = Speaker(voice=17, name="Cyllene", category="female")
    Leucosia = Speaker(voice=95, name="Leucosia", category="female")
    Crina = Speaker(voice=44, name="Crina", category="female")
    Hespe = Speaker(voice=80, name="Hespe", category="female")
    Ida = Speaker(voice=106, name="Ida", category="female")
    Alseid = Speaker(voice=6, name="Alseid", category="male")
    Daphnis = Speaker(voice=10, name="Daphnis", category="male")
    Echo = Speaker(voice=16, name="Echo", category="male")
    Thel = Speaker(voice=41, name="Thel", category="male")
    Nomios = Speaker(voice=77, name="Nomios", category="male")
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
