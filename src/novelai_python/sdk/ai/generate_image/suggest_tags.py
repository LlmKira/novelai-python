# @Time    : 2025/7/7 下午20:11
# @Author  : TimmekHW
# @File    : suggest_tags.py

import logging
import os
from typing import Literal

import curl_cffi
from curl_cffi.requests import AsyncSession
from pydantic import Field, PrivateAttr

from novelai_python.sdk.ai._enum import Model

from ...._exceptions import APIError, SessionHttpError
from ...._response.ai.generate_image import SuggestTagsResp
from ....credential import CredentialBase
from ....credential._base import IMPERSONATE, browser_headers
from ....metrics import get_metrics
from ...schema import ApiBaseModel, use_session

logger = logging.getLogger(__name__)


class SuggestTags(ApiBaseModel):
    _endpoint: str = PrivateAttr("https://image.novelai.net")
    model: Model | str = Field(default=Model.NAI_DIFFUSION_4_5_FULL, description="The image model")
    prompt: str = Field(..., description="The incomplete tag query")
    lang: Literal["en", "jp"] = Field(default="en", description="The language of the tag query")

    @property
    def base_url(self) -> str:
        return f"{self.endpoint.strip('/')}/ai/generate-image/suggest-tags"

    async def request(
        self, session: AsyncSession | CredentialBase | None = None, *, override_headers: dict | None = None
    ) -> SuggestTagsResp:
        """
        Request to get tag suggestions for image generation

        :param session: Session object for making requests
        :param override_headers: Optional headers to override defaults
        :return: SuggestTagsResp containing tag suggestions
        :raises AuthError: If authentication fails
        :raises APIError: If API returns an error
        :raises SessionHttpError: If session/network error occurs
        """
        # Prepare request data
        request_data = self.model_dump(mode="json", exclude_none=True)

        # Create session if not provided
        if session is None:
            # Anonymous call: same Chrome fingerprint as the credentials, never the
            # environment's system proxy; only an explicit NOVELAI_PROXY is used.
            px = os.environ.get("NOVELAI_PROXY")
            async with AsyncSession(
                impersonate=IMPERSONATE,
                trust_env=False,
                headers=browser_headers(),
                proxies={"http": px, "https": px} if px else None,
            ) as sess:
                return await self._make_request(sess, request_data, override_headers)
        else:
            async with use_session(session) as sess:
                return await self._make_request(sess, request_data, override_headers)

    async def _make_request(self, sess, request_data, override_headers):
        if override_headers:
            sess.headers.clear()
            sess.headers.update(override_headers)

        async with get_metrics().observe(self.base_url, self.model) as observed:
            try:
                # params= percent-encodes: a prompt holds "&", "#", "+" and non-ASCII text
                response = await sess.get(self.base_url, params=request_data)
                observed.report(response.status_code)

                if response.status_code != 200:
                    self._raise_for_status(
                        response.status_code,
                        response.content,
                        request_data,
                        self._legacy_400_as_auth,
                    )

                return SuggestTagsResp.model_validate_json(response.content)

            except curl_cffi.requests.errors.RequestsError as exc:
                logger.exception(exc)
                raise SessionHttpError("A RequestsError occurred (e.g., SSL error). Try again later.") from exc
            except APIError:
                raise  # not an unexpected error: keep it out of the handler below
            except Exception as e:
                logger.exception("Unexpected error occurred during the request.")
                raise Exception("An unexpected error occurred.") from e
