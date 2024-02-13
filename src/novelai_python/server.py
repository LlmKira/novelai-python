# -*- coding: utf-8 -*-
# @Time    : 2024/1/30 下午11:05
# @Author  : sudoskys
# @File    : server.py
# @Software: PyCharm
import io
import sys
import zipfile

import uvicorn
from fastapi import FastAPI, Depends, Security
from fastapi.security import APIKeyHeader
from loguru import logger
from starlette.responses import JSONResponse, StreamingResponse

from .credential import JwtCredential, SecretStr
from .sdk.ai.generate_image import GenerateImageInfer
from .sdk.ai.generate_image.suggest_tags import SuggestTags
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
        _result = await req.request(session=get_session(current_token), remove_sign=True)
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


@app.get("/ai/generate_image/suggest_tags")
async def suggest_tags(
        req: SuggestTags,
        current_token: str = Depends(get_current_token)
):
    """
    生成建议
    :param current_token: Authorization
    :param req: SuggestTags
    :return:
    """
    try:
        _result = await req.request(session=get_session(current_token))
        return _result.model_dump()
    except Exception as e:
        logger.exception(e)
        return JSONResponse(status_code=500, content=e.__dict__)


@app.post("/ai/generate_image")
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
        _result = await req.request(session=get_session(current_token), remove_sign=True)
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
    server_host = opts.get("-h", "0.0.0.0")
    server_port = int(opts.get("-p", 10087))
    print(f"Docs: http://{server_host}:{server_port}/docs")
    uvicorn.run(app, host=server_host, port=server_port)
