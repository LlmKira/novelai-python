# @Time    : 2024/1/30 下午11:05
# @Author  : sudoskys
# @File    : server.py

import io
import logging
import sys
import zipfile
from typing import Literal

try:
    import uvicorn
    from fastapi import Depends, FastAPI, Security
    from fastapi.security import APIKeyHeader
    from starlette.responses import JSONResponse, StreamingResponse
except ImportError as e:  # pragma: no cover
    raise ImportError('The server needs extra packages: pip install "novelai-python[server]"') from e

from novelai_python import LLMStream, LLMStreamResp
from novelai_python.sdk.ai.augment_image import AugmentImageInfer, Moods, ReqType

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
session = {}


def get_session(token: str):
    if token not in session:
        session[token] = JwtCredential(jwt_token=SecretStr(token))
    return session[token]


def get_current_token(auth_key: str = Security(token_key)):
    return auth_key


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
    try:
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
    except Exception as e:
        logger.exception(e)
        return JSONResponse(status_code=500, content=e.__dict__)


@app.get("/user/trial-status")
async def trial_status(current_token: str = Depends(get_current_token)):
    """
    Free-trial counters
    :param current_token: Authorization
    :return:
    """
    try:
        result = await TrialStatus().request(session=get_session(current_token))
        return result.model_dump()
    except Exception as e:
        logger.exception(e)
        return JSONResponse(status_code=500, content=e.__dict__)


@app.get("/user/data")
async def user_data(current_token: str = Depends(get_current_token)):
    """
    Aggregated account data (subscription + information + priority)
    :param current_token: Authorization
    :return:
    """
    try:
        result = await UserData().request(session=get_session(current_token))
        return result.model_dump()
    except Exception as e:
        logger.exception(e)
        return JSONResponse(status_code=500, content=e.__dict__)


@app.post("/user/login")
async def login(req: Login):
    """
    用户登录
    :param req: Login
    :return:
    """
    try:
        result = await req.request()
        return result.model_dump()
    except Exception as e:
        logger.exception(e)
        return JSONResponse(status_code=500, content=e.__dict__)


@app.get("/user/information")
async def information(current_token: str = Depends(get_current_token)):
    """
    用户信息
    :param current_token: Authorization
    :return:
    """
    try:
        result = await Information().request(session=get_session(current_token))
        return result.model_dump()
    except Exception as e:
        logger.exception(e)
        return JSONResponse(status_code=500, content=e.__dict__)


@app.get("/user/subscription")
async def subscription(current_token: str = Depends(get_current_token)):
    """
    订阅信息
    :param current_token: Authorization
    :return:
    """
    try:
        result = await Subscription().request(session=get_session(current_token))
        return result.model_dump()
    except Exception as e:
        logger.exception(e)
        return JSONResponse(status_code=500, content=e.__dict__)


@app.post("/ai/upscale")
async def upscale(req: Upscale, current_token: str = Depends(get_current_token)):
    """
    生成图片
    :param current_token: Authorization
    :param req: Upscale
    :return:
    """
    try:
        result = await req.request(session=get_session(current_token))
        zip_file_bytes = io.BytesIO()
        with zipfile.ZipFile(zip_file_bytes, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
            file = result.files  # ONLY TUPLE
            if file is None:
                raise ValueError("The upscale response holds no image")
            zip_file.writestr(zinfo_or_arcname=file[0], data=file[1])
        # return the zip file
        zip_file_bytes.seek(0)
        return StreamingResponse(
            zip_file_bytes,
            media_type="application/zip",
            headers={"Content-Disposition": "attachment;filename=image.zip"},
        )
    except Exception as e:
        logger.exception(e)
        return JSONResponse(status_code=500, content=e.__dict__)


@app.get("/ai/generate-image/suggest_tags")
async def suggest_tags(model: Model, prompt: str, current_token: str = Depends(get_current_token)):
    """
    生成建议
    :param current_token: Authorization
    :param model: Model
    :param prompt: str
    :return:
    """
    try:
        req = SuggestTags(model=model, prompt=prompt)
        result = await req.request(session=get_session(current_token))
        return result.model_dump()
    except Exception as e:
        logger.exception(e)
        return JSONResponse(status_code=500, content=e.__dict__)


@app.post("/ai/generate-image")
async def generate_image(req: GenerateImageInfer, current_token: str = Depends(get_current_token)):
    """
    生成图片
    :param current_token: Authorization
    :param req: GenerateImageInfer
    :return:
    """
    try:
        result = await req.request(session=get_session(current_token))
        zip_file_bytes = io.BytesIO()
        with zipfile.ZipFile(zip_file_bytes, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
            for file in result.files or []:
                zip_file.writestr(zinfo_or_arcname=file[0], data=file[1])
        # return the zip file
        zip_file_bytes.seek(0)
        return StreamingResponse(
            zip_file_bytes,
            media_type="application/zip",
            headers={"Content-Disposition": "attachment;filename=image.zip"},
        )
    except Exception as e:
        logger.exception(e)
        return JSONResponse(status_code=500, content=e.__dict__)


@app.post("/ai/generate-stream")
async def generate_stream(req: LLMStream, current_token: str = Depends(get_current_token)):
    """
    流式生成
    :param current_token: Authorization
    :param req: LLMStream
    :return:
    """

    async def generator():
        agent = req
        session = get_session(current_token)
        generator = agent.request(session=session)
        async for data in generator:
            data: LLMStreamResp
            yield data.text or ""

    return StreamingResponse(generator())


@app.post("/ai/generate")
async def generate(req: LLM, current_token: str = Depends(get_current_token)):
    """
    对话生成
    :param current_token: Authorization
    :param req: LLM
    :return:
    """
    try:
        result = await req.request(session=get_session(current_token))
        return result.model_dump()
    except Exception as e:
        logger.exception(e)
        return JSONResponse(status_code=500, content=e.__dict__)


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
    try:
        req = VoiceGenerate(text=text, voice=voice, seed=seed, opus=opus, version=version)
        result = await req.request(session=get_session(current_token))
        return StreamingResponse(
            io.BytesIO(result.audio),
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment;filename=audio.mp3"},
        )
    except Exception as e:
        logger.exception(e)
        return JSONResponse(status_code=500, content=e.__dict__)


@app.post("/ai/augment-image")
async def augment_image(
    req_type: ReqType,
    image: bytes,
    mood: Moods | None = None,
    prompt: str | None = None,
    defry: int | None = None,
    current_token: str = Depends(get_current_token),
):
    """
    生成图片
    :param current_token: Authorization
    :param req_type: ReqType
    :param image: bytes
    :param mood: Optional[Moods]
    :param prompt: Optional[str]
    :param defry: Optional[int]
    :return:
    """
    try:
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
        # return the zip file
        zip_file_bytes.seek(0)
        return StreamingResponse(
            zip_file_bytes,
            media_type="application/zip",
            headers={"Content-Disposition": "attachment;filename=image.zip"},
        )
    except Exception as e:
        logger.exception(e)
        return JSONResponse(status_code=500, content=e.__dict__)


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
