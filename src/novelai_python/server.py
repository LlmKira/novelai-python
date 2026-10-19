# @Time    : 2024/1/30 下午11:05
# @Author  : sudoskys
# @File    : server.py

import io
import logging
import sys
import zipfile
from collections import OrderedDict
from typing import Annotated, Literal

try:
    import uvicorn
    from fastapi import Body, Depends, FastAPI, Request, Security
    from fastapi.security import APIKeyHeader
    from starlette.responses import JSONResponse, StreamingResponse
except ImportError as e:  # pragma: no cover
    raise ImportError('The server needs extra packages: pip install "novelai-python[server]"') from e

from pydantic import ValidationError

from novelai_python import LLMStream, LLMStreamResp
from novelai_python.sdk.ai.augment_image import AugmentImageInfer, Moods, ReqType

from ._exceptions import APIError, NovelAiError
from .credential import JwtCredential, SecretStr
from .sdk.ai.generate import LLM
from .sdk.ai.generate_image import GenerateImageInfer, Model
from .sdk.ai.generate_image.suggest_tags import SuggestTags
from .sdk.ai.generate_voice import VoiceGenerate
from .sdk.ai.upscale import Upscale
from .sdk.user.data import UserData
from .sdk.user.information import Information
from .sdk.user.login import Login
from .sdk.user.subscription import Subscription
from .sdk.user.trial_status import TrialStatus
from .utils.daily_limit import get_default_limiter

logger = logging.getLogger(__name__)

app = FastAPI()
token_key = APIKeyHeader(name="Authorization")

SESSION_CACHE_LIMIT = 128
session: OrderedDict[str, JwtCredential] = OrderedDict()


def get_session(token: str) -> JwtCredential:
    credential = session.get(token)
    if credential is None:
        credential = JwtCredential(jwt_token=SecretStr(token))
        session[token] = credential
        if len(session) > SESSION_CACHE_LIMIT:
            session.popitem(last=False)
    else:
        session.move_to_end(token)
    return credential


def get_current_token(auth_key: str = Security(token_key)):
    # "Bearer <token>" or the bare token; the credential adds "Bearer " itself
    scheme, _, token = auth_key.partition(" ")
    return token.strip() if scheme.lower() == "bearer" and token.strip() else auth_key


@app.exception_handler(APIError)
async def api_error_handler(_request: Request, exc: APIError):
    """Render SDK errors once, with the status the upstream reported."""
    try:
        status = int(exc.code) if exc.code is not None else 500
    except (TypeError, ValueError):
        status = 500
    if not 400 <= status <= 599:
        status = 500
    if status >= 500:
        logger.exception(exc)
    else:
        logger.warning("%s: %s", type(exc).__name__, exc.message)
    return JSONResponse(status_code=status, content={"message": exc.message, "code": exc.code})


@app.exception_handler(NovelAiError)
async def novelai_error_handler(_request: Request, exc: NovelAiError):
    logger.exception(exc)
    return JSONResponse(status_code=500, content={"message": exc.message})


@app.exception_handler(ValidationError)
async def validation_error_handler(_request: Request, exc: ValidationError):
    """A request model built inside a route (from query parameters) rejected its input."""
    return JSONResponse(status_code=422, content={"detail": exc.errors(include_url=False, include_context=False)})


@app.exception_handler(Exception)
async def unexpected_error_handler(_request: Request, exc: Exception):
    logger.exception(exc)
    return JSONResponse(status_code=500, content={"message": "Internal server error"})


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/limit")
async def image_limit(current_token: str = Depends(get_current_token)):
    """
    State of the process-wide image budget (requests opt in with ``limiter=True``)
    :return:
    """
    limiter = get_default_limiter()
    return limiter.status() if limiter else {"enabled": False}


@app.get("/user/anlas")
async def anlas(current_token: str = Depends(get_current_token)):
    """
    Anlas balance + subscription tier, for monitoring
    :param current_token: Authorization
    :return:
    """
    result = await Subscription().request(session=get_session(current_token))
    return {
        "anlas_left": result.anlas_left,
        "fixed": result.trainingStepsLeft.fixedTrainingStepsLeft,
        "purchased": result.trainingStepsLeft.purchasedTrainingSteps,
        "tier": result.tier_name,
        "active": result.is_active,
        "unlimited_image_generation": result.is_unlimited_image_generation,
        "expires_at": result.expiresAt,
    }


@app.get("/user/trial-status")
async def trial_status(current_token: str = Depends(get_current_token)):
    """
    Free-trial counters
    :param current_token: Authorization
    :return:
    """
    result = await TrialStatus().request(session=get_session(current_token))
    return result.model_dump()


@app.get("/user/data")
async def user_data(current_token: str = Depends(get_current_token)):
    """
    Aggregated account data (subscription + information + priority)
    :param current_token: Authorization
    :return:
    """
    result = await UserData().request(session=get_session(current_token))
    return result.model_dump()


@app.post("/user/login")
async def login(req: Login):
    """
    用户登录
    :param req: Login
    :return:
    """
    result = await req.request()
    return result.model_dump()


@app.get("/user/information")
async def information(current_token: str = Depends(get_current_token)):
    """
    用户信息
    :param current_token: Authorization
    :return:
    """
    result = await Information().request(session=get_session(current_token))
    return result.model_dump()


@app.get("/user/subscription")
async def subscription(current_token: str = Depends(get_current_token)):
    """
    订阅信息
    :param current_token: Authorization
    :return:
    """
    result = await Subscription().request(session=get_session(current_token))
    return result.model_dump()


@app.post("/ai/upscale")
async def upscale(req: Upscale, current_token: str = Depends(get_current_token)):
    """
    生成图片
    :param current_token: Authorization
    :param req: Upscale
    :return:
    """
    result = await req.request(session=get_session(current_token))
    file = result.files
    if file is None:
        raise ValueError("The upscale response holds no image")
    zip_file_bytes = io.BytesIO()
    with zipfile.ZipFile(zip_file_bytes, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr(zinfo_or_arcname=file[0], data=file[1])
    zip_file_bytes.seek(0)
    return StreamingResponse(
        zip_file_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment;filename=image.zip"},
    )


@app.get("/ai/generate-image/suggest_tags")
async def suggest_tags(model: Model, prompt: str, current_token: str = Depends(get_current_token)):
    """
    生成建议
    :param current_token: Authorization
    :param model: Model
    :param prompt: str
    :return:
    """
    result = await SuggestTags(model=model, prompt=prompt).request(session=get_session(current_token))
    return result.model_dump()


@app.post("/ai/generate-image")
async def generate_image(req: GenerateImageInfer, current_token: str = Depends(get_current_token)):
    """
    生成图片
    :param current_token: Authorization
    :param req: GenerateImageInfer
    :return:
    """
    result = await req.request(session=get_session(current_token))
    zip_file_bytes = io.BytesIO()
    with zipfile.ZipFile(zip_file_bytes, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        for file in result.files or []:
            zip_file.writestr(zinfo_or_arcname=file[0], data=file[1])
    zip_file_bytes.seek(0)
    return StreamingResponse(
        zip_file_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment;filename=image.zip"},
    )


@app.post("/ai/generate-stream")
async def generate_stream(req: LLMStream, current_token: str = Depends(get_current_token)):
    """
    流式生成
    :param current_token: Authorization
    :param req: LLMStream
    :return:
    """

    stream = req.request(session=get_session(current_token))
    # read the first event before the 200 goes out, so an upstream error gets its own status
    first: LLMStreamResp | None = await anext(aiter(stream), None)

    async def body():
        if first is None:
            return
        yield first.text or ""
        async for data in stream:
            yield data.text or ""

    return StreamingResponse(body(), media_type="text/plain; charset=utf-8")


@app.post("/ai/generate")
async def generate(req: LLM, current_token: str = Depends(get_current_token)):
    """
    对话生成
    :param current_token: Authorization
    :param req: LLM
    :return:
    """
    result = await req.request(session=get_session(current_token))
    return result.model_dump()


@app.get("/ai/generate-voice")
async def generate_voice(
    text: str,
    voice: int = -1,
    seed: str | None = None,
    opus: bool = False,
    version: Literal["v2", "v1"] | str = "v2",
    current_token: str = Depends(get_current_token),
):
    """
    生成图片
    :param current_token: Authorization
    :param text: str
    :param voice: int
    :param seed: Optional[str]
    :param opus: bool
    :param version: Union[Literal["v2", "v1"], str]
    :return:
    """
    req = VoiceGenerate(text=text, voice=voice, seed=seed, opus=opus, version=version)
    result = await req.request(session=get_session(current_token))
    # opus=true is WebM/Opus, as the web client plays it; otherwise MP3
    media_type, filename = ("audio/webm", "audio.webm") if opus else ("audio/mpeg", "audio.mp3")
    return StreamingResponse(
        io.BytesIO(result.audio),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment;filename={filename}"},
    )


@app.post("/ai/augment-image")
async def augment_image(
    req_type: ReqType,
    image: Annotated[bytes, Body(media_type="application/octet-stream")],
    mood: Moods | None = None,
    prompt: str | None = None,
    defry: int | None = None,
    current_token: str = Depends(get_current_token),
):
    """
    生成图片
    :param current_token: Authorization
    :param req_type: ReqType
    :param image: the image file as the request body
    :param mood: Optional[Moods]
    :param prompt: Optional[str]
    :param defry: Optional[int]
    :return:
    """
    req = AugmentImageInfer.build(
        req_type=req_type,
        image=image,
        mood=mood,
        prompt=prompt,
        defry=defry,
    )
    result = await req.request(session=get_session(current_token))
    zip_file_bytes = io.BytesIO()
    with zipfile.ZipFile(zip_file_bytes, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        for file in result.files or []:
            zip_file.writestr(zinfo_or_arcname=file[0], data=file[1])
    zip_file_bytes.seek(0)
    return StreamingResponse(
        zip_file_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment;filename=image.zip"},
    )


# 获取输入参数
def usage() -> None:
    print("Usage: python -m novelai_python.server -h <host> -p <port>")
    sys.exit(0)


if __name__ == "__main__":
    import getopt

    opts = {}
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h:p:", ["host=", "port="])
    except getopt.GetoptError:
        usage()
    opts = dict(opts)
    server_host = opts.get("-h", "127.0.0.1")
    server_port = int(opts.get("-p", 10087))
    print(f"Docs: http://{server_host}:{server_port}/docs")
    uvicorn.run(app, host=server_host, port=server_port)
