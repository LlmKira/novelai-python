# -*- coding: utf-8 -*-
# @Time    : 2024/2/8 下午3:10
# @Author  : sudoskys
# @File    : information.py
# @Software: PyCharm

from pydantic import Field

from ..schema import RespBase


class InformationResp(RespBase):
    emailVerified: bool = Field(..., description="Email verification status")
    emailVerificationLetterSent: bool = Field(..., description="Email verification letter sent status")
    trialActivated: bool = Field(..., description="Trial activation status")
    trialActionsLeft: int = Field(..., description="Number of trial actions left")
    trialImagesLeft: int = Field(..., description="Number of trial images left")
    accountCreatedAt: int = Field(..., description="Account creation time")
