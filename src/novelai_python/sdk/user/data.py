# @File    : data.py


import logging
from typing import ClassVar

from curl_cffi.requests import AsyncSession
from pydantic import PrivateAttr

from ..._response.user.data import UserDataResp
from ...credential import CredentialBase
from ..schema import ApiBaseModel

logger = logging.getLogger(__name__)


class UserData(ApiBaseModel):
    _endpoint: str = PrivateAttr("https://image.novelai.net")
    _legacy_400_as_auth: ClassVar[bool] = False

    @property
    def base_url(self) -> str:
        return f"{self.endpoint.strip('/')}/user/data"

    @property
    def endpoint(self):
        return self._endpoint

    @endpoint.setter
    def endpoint(self, value) -> None:
        self._endpoint = value

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
        return UserDataResp.model_validate_json(response.content)
