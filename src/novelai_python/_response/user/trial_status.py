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

    trialActivated: bool | None = Field(default=None, description="Whether the free trial is active")
    trialActionsLeft: int | None = Field(default=None, description="Text generations left in the trial")
    trialImagesLeft: int | None = Field(default=None, description="Image generations left in the trial")
    # current shape (live 2026-10-17)
    used_text_actions: int | None = None
    remaining_text_actions: int | None = None
    used_image_actions: int | None = None
    remaining_image_actions: int | None = None
    eligible_for_text_gens: bool | None = None
    eligible_for_image_gens: bool | None = None
    trial_activated: bool | None = None
