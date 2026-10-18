# @Time    : 2024/2/7 上午10:04
# @Author  : sudoskys
# @File    : subscription.py.py


import logging

from curl_cffi.requests import AsyncSession
from pydantic import PrivateAttr

from ..._response.user.subscription import SubscriptionResp
from ...credential import CredentialBase
from ..schema import ApiBaseModel

logger = logging.getLogger(__name__)


class Subscription(ApiBaseModel):
    _endpoint: str = PrivateAttr("https://image.novelai.net")

    @property
    def base_url(self) -> str:
        return f"{self.endpoint.strip('/')}/user/subscription"

    async def request(
        self, session: AsyncSession | CredentialBase, *, override_headers: dict | None = None
    ) -> SubscriptionResp:
        """
        Request to get user subscription information
        :param override_headers:
        :param session:
        :return:
        """
        response = await self._send(session, "GET", override_headers=override_headers)
        return SubscriptionResp.model_validate_json(response.content)
