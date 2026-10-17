# @Time    : 2024/2/8 下午3:09
# @Author  : sudoskys
# @File    : information.py


import logging

from curl_cffi.requests import AsyncSession
from pydantic import PrivateAttr

from ..._response.user.information import InformationResp
from ...credential import CredentialBase
from ..schema import ApiBaseModel

logger = logging.getLogger(__name__)


class Information(ApiBaseModel):
    _endpoint: str = PrivateAttr("https://image.novelai.net")

    @property
    def base_url(self) -> str:
        return f"{self.endpoint.strip('/')}/user/information"

    @property
    def endpoint(self):
        return self._endpoint

    @endpoint.setter
    def endpoint(self, value) -> None:
        self._endpoint = value

    async def request(
        self, session: AsyncSession | CredentialBase, *, override_headers: dict | None = None
    ) -> InformationResp:
        """
        Request to get user subscription information
        :param override_headers:
        :param session:
        :return:
        """
        response = await self._send(session, "GET", override_headers=override_headers)
        return InformationResp.model_validate_json(response.content)
