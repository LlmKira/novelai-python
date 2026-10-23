# @File    : data.py


import logging
from typing import ClassVar

from curl_cffi.requests import AsyncSession
from pydantic import PrivateAttr

from ..._response.user.data import UserDataResp
from ...credential import CredentialBase
from ...metrics import account_label, get_metrics
from ..schema import ApiBaseModel

logger = logging.getLogger(__name__)


class UserData(ApiBaseModel):
    _endpoint: str = PrivateAttr("https://image.novelai.net")
    _legacy_400_as_auth: ClassVar[bool] = False

    @property
    def base_url(self) -> str:
        return f"{self.endpoint.strip('/')}/user/data"

    async def request(
        self, session: AsyncSession | CredentialBase, *, override_headers: dict | None = None
    ) -> UserDataResp:
        """
        Aggregated account data (subscription, information, priority, ...).
        One call instead of /user/subscription + /user/information.
        :param override_headers:
        :param session:
        :return:
        """
        response = await self._send(session, "GET", override_headers=override_headers)
        result = UserDataResp.model_validate_json(response.content)
        get_metrics().observe_subscription(result.subscription, account_label(session))
        return result
