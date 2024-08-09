# -*- coding: utf-8 -*-
# @Time    : 2024/1/30 下午11:05
# @Author  : sudoskys
# @File    : server.py

import io
import sys
import zipfile
from typing import Optional, Literal, Union

import uvicorn
from fastapi import FastAPI, Depends, Security
from fastapi.security import APIKeyHeader
from loguru import logger
from starlette.responses import JSONResponse, StreamingResponse

from novelai_python import LLMStream, LLMStreamResp
from novelai_python.sdk.ai.augment_image import ReqType, Moods, AugmentImageInfer
from .credential import JwtCredential, SecretStr
from .sdk.ai.generate import LLM
from .sdk.ai.generate_image import GenerateImageInfer, Model
from .sdk.ai.generate_image.suggest_tags import SuggestTags
from .sdk.ai.generate_voice import VoiceGenerate
from .sdk.ai.upscale import Upscale
from .sdk.user.information import Information
from .sdk.user.login import Login
from .sdk.user.subscription import Subscription

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


@app.post("/user/login")
async def login(
        req: Login
):
    """
    用户登录
    :param req: Login
    :return:
    """
    try:
        _result = await req.request()
        return _result.model_dump()
    except Exception as e:
        logger.exception(e)
        return JSONResponse(status_code=500, content=e.__dict__)


@app.get("/user/information")
async def information(
        current_token: str = Depends(get_current_token)
):
    """
    用户信息
    :param current_token: Authorization
    :return:
    """
    try:
        _result = await Information().request(session=get_session(current_token))
        return _result.model_dump()
    except Exception as e:
        logger.exception(e)
        return JSONResponse(status_code=500, content=e.__dict__)


@app.get("/user/subscription")
async def subscription(
        current_token: str = Depends(get_current_token)
):
    """
    订阅信息
    :param current_token: Authorization
    :return:
    """
    try:
        _result = await Subscription().request(session=get_session(current_token))
        return _result.model_dump()
    except Exception as e:
        logger.exception(e)
        return JSONResponse(status_code=500, content=e.__dict__)


@app.post("/ai/upscale")
async def upscale(
        req: Upscale,
        current_token: str = Depends(get_current_token)
):
    """
    生成图片
    :param current_token: Authorization
    :param req: Upscale
    :return:
    """
    try:
        _result = await req.request(session=get_session(current_token))
        zip_file_bytes = io.BytesIO()
        with zipfile.ZipFile(zip_file_bytes, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
            file = _result.files  # ONLY TUPLE
            zip_file.writestr(zinfo_or_arcname=file[0], data=file[1])
        # return the zip file
        zip_file_bytes.seek(0)
        return StreamingResponse(zip_file_bytes, media_type='application/zip', headers={
            'Content-Disposition': 'attachment;filename=image.zip'
        })
    except Exception as e:
        logger.exception(e)
        return JSONResponse(status_code=500, content=e.__dict__)


@app.get("/ai/generate-image/suggest_tags")
async def suggest_tags(
        model: Model,
        prompt: str,
        current_token: str = Depends(get_current_token)
):
    """
    生成建议
    :param current_token: Authorization
    :param model: Model
    :param prompt: str
    :return:
    """
    try:
        req = SuggestTags(model=model, prompt=prompt)
        _result = await req.request(session=get_session(current_token))
        return _result.model_dump()
    except Exception as e:
        logger.exception(e)
        return JSONResponse(status_code=500, content=e.__dict__)


@app.post("/ai/generate-image")
async def generate_image(
        req: GenerateImageInfer,
        current_token: str = Depends(get_current_token)
):
    """
    生成图片
    :param current_token: Authorization
    :param req: GenerateImageInfer
    :return:
    """
    try:
        _result = await req.request(session=get_session(current_token))
        zip_file_bytes = io.BytesIO()
        with zipfile.ZipFile(zip_file_bytes, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
            for file in _result.files:
                zip_file.writestr(zinfo_or_arcname=file[0], data=file[1])
        # return the zip file
        zip_file_bytes.seek(0)
        return StreamingResponse(zip_file_bytes, media_type='application/zip', headers={
            'Content-Disposition': 'attachment;filename=image.zip'
        })
    except Exception as e:
        logger.exception(e)
        return JSONResponse(status_code=500, content=e.__dict__)


@app.post("/ai/generate-stream")
async def generate(
        req: LLMStream,
        current_token: str = Depends(get_current_token)
):
    """
    流式生成
    :param current_token: Authorization
    :param req: LLMStream
    :return:
    """

    async def generator():
        agent = req
        session = await get_session(current_token)  # Assume 'get_session()' is a function to get session by token
        generator = agent.request(session=session)
        async for data in generator:
            data: LLMStreamResp
            yield data.text  # Yield data for streaming response

    return StreamingResponse(generator())


@app.post("/ai/generate")
async def generate(
        req: LLM,
        current_token: str = Depends(get_current_token)
):
    """
    对话生成
    :param current_token: Authorization
    :param req: LLM
    :return:
    """
    try:
        _result = await req.request(session=get_session(current_token))
        return _result.model_dump()
    except Exception as e:
        logger.exception(e)
        return JSONResponse(status_code=500, content=e.__dict__)


@app.get("/ai/generate-voice")
async def generate_voice(
        text: str,
        voice: int = -1,
        seed: Optional[str] = None,
        opus: bool = False,
        version: Union[Literal["v2", "v1"], str] = "v2",
        current_token: str = Depends(get_current_token)
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
        _result = await req.request(session=get_session(current_token))
        return StreamingResponse(io.BytesIO(_result.audio), media_type='audio/mpeg', headers={
            'Content-Disposition': 'attachment;filename=audio.mp3'
        })
    except Exception as e:
        logger.exception(e)
        return JSONResponse(status_code=500, content=e.__dict__)


@app.post("/ai/augment-image")
async def augment_image(
        req_type: ReqType,
        image: bytes,
        mood: Optional[Moods] = None,
        prompt: Optional[str] = None,
        defry: Optional[int] = None,
        current_token: str = Depends(get_current_token)
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
        _result = await req.request(session=get_session(current_token))
        zip_file_bytes = io.BytesIO()
        with zipfile.ZipFile(zip_file_bytes, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
            for file in _result.files:
                zip_file.writestr(zinfo_or_arcname=file[0], data=file[1])
        # return the zip file
        zip_file_bytes.seek(0)
        return StreamingResponse(zip_file_bytes, media_type='application/zip', headers={
            'Content-Disposition': 'attachment;filename=image.zip'
        })
    except Exception as e:
        logger.exception(e)
        return JSONResponse(status_code=500, content=e.__dict__)


# 获取输入参数
def usage():
    print("Usage: python -m novelai_python.server -h <host> -p <port>")
    sys.exit(0)


if __name__ == '__main__':
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
