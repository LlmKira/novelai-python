# @File    : trial_status.py


import curl_cffi
from curl_cffi.requests import AsyncSession
from loguru import logger
from pydantic import PrivateAttr

from ..._exceptions import APIError, AuthError, SessionHttpError
from ..._response.user.trial_status import TrialStatusResp
from ...credential import CredentialBase
from ..schema import ApiBaseModel


class TrialStatus(ApiBaseModel):
    _endpoint: str = PrivateAttr("https://text.novelai.net")

    @property
    def base_url(self) -> str:
        return f"{self.endpoint.strip('/')}/ai/trial-status"

    @property
    def endpoint(self):
        return self._endpoint

    @endpoint.setter
    def endpoint(self, value) -> None:
        self._endpoint = value

    async def request(
        self, session: AsyncSession | CredentialBase, *, override_headers: dict | None = None
    ) -> TrialStatusResp:
        """
        Free-trial counters (text / image actions left).
        :param override_headers:
        :param session:
        :return:
        """
        request_data = {}
        async with session if isinstance(session, AsyncSession) else await session.get_session() as sess:
            if override_headers:
                sess.headers.clear()
                sess.headers.update(override_headers)
            logger.debug("TrialStatus")
            try:
                self.ensure_session_has_get_method(sess)
                response = await sess.get(url=self.base_url)
                if "application/json" not in response.headers.get("Content-Type") or response.status_code != 200:
                    error_message = await self.handle_error_response(response=response, request_data=request_data)
                    status_code = error_message.get("statusCode", response.status_code)
                    message = error_message.get("message", "Unknown error")
                    if status_code in [400, 401, 402]:
                        raise AuthError(message, request=request_data, code=status_code, response=error_message)
                    raise APIError(message, request=request_data, code=status_code, response=error_message)
                return TrialStatusResp.model_validate_json(response.content)
            except curl_cffi.requests.errors.RequestsError as exc:
                logger.exception(exc)
                raise SessionHttpError(
                    "An AsyncSession RequestsError occurred, maybe SSL error. Try again later!"
                ) from exc
            except APIError as e:
                raise e
            except Exception as e:
                logger.opt(exception=e).exception("An Unexpected error occurred")
                raise e
