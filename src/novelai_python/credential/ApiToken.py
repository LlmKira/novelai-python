# @Time    : 2024/2/8 下午3:05
# @Author  : sudoskys
# @File    : ApiToken.py


import logging

from pydantic import Field, SecretStr, field_validator

from ._base import BearerCredential

logger = logging.getLogger(__name__)


class ApiCredential(BearerCredential):
    """
    ApiCredential sends a persistent API token (pst-...) as the bearer token.
    """

    api_token: SecretStr | None = Field(default=None, description="api token")

    def _token(self) -> str:
        if self.api_token is None:
            raise ValueError("api_token is not set")
        return self.api_token.get_secret_value()

    @field_validator("api_token")
    def check_api_token(cls, v: SecretStr | None):
        if v is not None and not v.get_secret_value().startswith("pst"):
            logger.warning("api_token should start with `pst-`")
        return v
