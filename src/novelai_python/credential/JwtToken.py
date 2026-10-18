# @Time    : 2024/1/26 上午11:04
# @Author  : sudoskys
# @File    : JwtToken.py


import logging

from pydantic import Field, SecretStr, field_validator

from ._base import BearerCredential

logger = logging.getLogger(__name__)


class JwtCredential(BearerCredential):
    """
    JwtCredential sends a JWT access token as the bearer token.
    """

    jwt_token: SecretStr | None = Field(default=None, description="jwt token")

    def _token(self) -> str:
        if self.jwt_token is None:
            raise ValueError("jwt_token is not set")
        return self.jwt_token.get_secret_value()

    @field_validator("jwt_token")
    def check_jwt_token(cls, v: SecretStr | None):
        if v is not None and not v.get_secret_value().startswith("ey"):
            logger.warning("jwt_token should start with ey")
        return v
