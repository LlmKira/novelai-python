# @File    : trial_status.py


from pydantic import ConfigDict, Field

from ..schema import RespBase


class TrialStatusResp(RespBase):
    """
    GET https://text.novelai.net/ai/trial-status

    The web client polls this next to /user/subscription. Field names are
    kept loose (extra fields allowed) because the payload is not documented.
    """

    model_config = ConfigDict(extra="allow")

    trialActivated: bool | None = Field(None, description="Whether the free trial is active")
    trialActionsLeft: int | None = Field(None, description="Text generations left in the trial")
    trialImagesLeft: int | None = Field(None, description="Image generations left in the trial")
