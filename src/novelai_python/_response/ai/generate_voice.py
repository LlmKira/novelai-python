from pydantic import BaseModel, ConfigDict


class VoiceResponse(BaseModel):
    meta: dict
    audio: bytes
    model_config = ConfigDict(extra="ignore", arbitrary_types_allowed=True)
