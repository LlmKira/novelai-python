# -*- coding: utf-8 -*-
# @File    : data.py

from typing import Optional, Any, Dict

from pydantic import ConfigDict, Field

from ..schema import RespBase
from .information import InformationResp
from .subscription import SubscriptionResp


class UserDataResp(RespBase):
    """
    GET https://image.novelai.net/user/data

    Aggregated account payload the web client loads right after sign-in.
    Nested blocks are optional and extra keys are kept.
    """
    model_config = ConfigDict(extra="allow")

    subscription: Optional[SubscriptionResp] = Field(None, description="Same shape as /user/subscription")
    information: Optional[InformationResp] = Field(None, description="Same shape as /user/information")
    priority: Optional[Dict[str, Any]] = Field(None, description="Queue priority block")
    keystore: Optional[Dict[str, Any]] = Field(None, description="Encrypted keystore block")
    settings: Optional[Any] = Field(None, description="Client settings blob")

    @property
    def anlas_left(self) -> Optional[int]:
        return self.subscription.anlas_left if self.subscription else None
