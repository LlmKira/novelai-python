# @File    : priority.py

from curl_cffi.requests import AsyncSession
from pydantic import BaseModel, Field, PrivateAttr

from ...credential import CredentialBase
from ..schema import ApiBaseModel


class PriorityResp(BaseModel):
    """GET /user/priority: the account's task priority balance."""

    maxPriorityActions: int | None = Field(None, description="Priority actions the balance refills to")
    nextRefillAt: int | None = Field(None, description="Next priority refill (UNIX timestamp)")
    taskPriority: float | None = Field(None, description="Current task priority")


class Priority(ApiBaseModel):
    _endpoint: str = PrivateAttr("https://image.novelai.net")

    @property
    def base_url(self) -> str:
        return f"{self.endpoint.strip('/')}/user/priority"

    async def request(
        self, session: AsyncSession | CredentialBase, *, override_headers: dict | None = None
    ) -> PriorityResp:
        """Current priority action balance and next refill time."""
        response = await self._send(session, "GET", override_headers=override_headers)
        return PriorityResp.model_validate_json(response.content)
