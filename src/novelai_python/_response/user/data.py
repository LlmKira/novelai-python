# @File    : data.py

from typing import Any

from pydantic import ConfigDict, Field

from ..schema import RespBase
from .information import InformationResp
from .priority import PriorityResp
from .subscription import SubscriptionResp


class UserDataResp(RespBase):
    """
    GET https://image.novelai.net/user/data

    Aggregated account payload the web client loads right after sign-in.
    Nested blocks are optional and extra keys are kept.
    """

    model_config = ConfigDict(extra="allow")

    subscription: SubscriptionResp | None = Field(default=None, description="Same shape as /user/subscription")
    information: InformationResp | None = Field(default=None, description="Same shape as /user/information")
    priority: PriorityResp | None = Field(default=None, description="Queue priority block")
    keystore: dict[str, Any] | None = Field(default=None, description="Encrypted keystore block")
    settings: Any | None = Field(default=None, description="Client settings blob")

    @property
    def anlas_left(self) -> int | None:
        return self.subscription.anlas_left if self.subscription else None
