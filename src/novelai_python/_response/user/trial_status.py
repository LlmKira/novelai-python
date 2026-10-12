# -*- coding: utf-8 -*-
# @File    : trial_status.py

from typing import Optional

from pydantic import ConfigDict, Field

from ..schema import RespBase


class TrialStatusResp(RespBase):
    """
    GET https://text.novelai.net/ai/trial-status

    The web client polls this next to /user/subscription. Field names are
    kept loose (extra fields allowed) because the payload is not documented.
    """
    model_config = ConfigDict(extra="allow")

    trialActivated: Optional[bool] = Field(None, description="Whether the free trial is active")
    trialActionsLeft: Optional[int] = Field(None, description="Text generations left in the trial")
    trialImagesLeft: Optional[int] = Field(None, description="Image generations left in the trial")
