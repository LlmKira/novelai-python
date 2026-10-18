# @Time    : 2024/2/8 下午3:10
# @Author  : sudoskys
# @File    : information.py


from typing import Any

from pydantic import ConfigDict, Field

from ..schema import RespBase


class InformationResp(RespBase):
    emailVerified: bool = Field(..., description="Email verification status")
    emailVerificationLetterSent: bool = Field(..., description="Email verification letter sent status")
    trialActivated: bool = Field(..., description="Trial activation status")
    trialActionsLeft: int = Field(..., description="Number of trial actions left")
    trialImagesLeft: int = Field(..., description="Number of trial images left")
    accountCreatedAt: int = Field(..., description="Account creation time")
    # The upstream payload carries more account flags; keep them instead of dropping them.
    banStatus: Any | None = None
    plainTextEmail: str | None = None
    loginMethod: str | None = None
    needsAddressChange: bool | None = None
    hasPlaintextEmail: bool | None = None

    model_config = ConfigDict(extra="allow")
