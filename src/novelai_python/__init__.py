# -*- coding: utf-8 -*-
# @Time    : 2023/11/18 上午12:18
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
import json
import random
from io import BytesIO
from typing import Optional, Union
from zipfile import ZipFile

import httpx
import shortuuid
from curl_cffi.requests import AsyncSession
from dotenv import load_dotenv
from loguru import logger
from pydantic import BaseModel, ConfigDict, PrivateAttr, field_validator, SecretStr

from .error import ServerError, AuthError
from .hash import NaiPic
from .schema import NaiResult

load_dotenv()


class CheckError(Exception):
    pass


class CurlSession(BaseModel):
    jwt_token: SecretStr
    _session: AsyncSession = None

    @property
    def session(self):
        if not self._session:
            self._session = AsyncSession(timeout=180, headers={
                "Authorization": f"Bearer {self.jwt_token.get_secret_value()}",
                "Content-Type": "application/json",
                "Origin": "https://novelai.net",
                "Referer": "https://novelai.net/",
            }, impersonate="chrome110")
        return self._session


class NovelAiInference(BaseModel):
    _endpoint: Optional[str] = PrivateAttr("https://api.novelai.net")
    _charge: bool = PrivateAttr(False)

    class Params(BaseModel):
        add_original_image: Optional[bool] = False
        cfg_rescale: Optional[int] = 0
        controlnet_strength: Optional[int] = 1
        dynamic_thresholding: Optional[bool] = False
        height: Optional[int] = 1216
        legacy: Optional[bool] = False
        legacy_v3_extend: Optional[bool] = False
        n_samples: Optional[int] = 1
        negative_prompt: Optional[str] = (
            "nsfw, lowres, {bad}, error, fewer, extra, missing, worst quality, jpeg artifacts, bad quality, "
            "watermark, unfinished, displeasing, chromatic aberration, signature, extra digits, artistic error, "
            "username, scan, [abstract], bad anatomy, bad hands, @_@, mismatched pupils, heart-shaped pupils, "
            "glowing eyes, nsfw, lowres, bad anatomy, bad hands, text, error,                        missing fingers, "
            "extra digit, fewer digits, cropped,                        worst quality, low quality, normal quality, "
            "jpeg artifacts, signature, watermark, username, blurry"
        )
        noise_schedule: Optional[str] = "native"
        params_version: Optional[int] = 1
        qualityToggle: Optional[bool] = True
        sampler: Optional[str] = "k_euler"
        scale: Optional[int] = 5
        seed: Optional[int] = -1
        sm: Optional[bool] = False
        sm_dyn: Optional[bool] = False
        steps: Optional[int] = 28
        ucPreset: Optional[int] = 0
        uncond_scale: Optional[int] = 1
        width: Optional[int] = 832

        @field_validator('seed')
        def seed_validator(cls, v: int):
            if v == -1:
                v = random.randint(0, 2 ** 32 - 1)
            return v

        @field_validator('sampler')
        def sampler_validator(cls, v: str):
            if v not in ["k_euler", "k_euler_ancestral", "k_dpmpp_2m", "k_dpmpp_sde", "ddim_v3"]:
                raise ValueError("Invalid sampler.")
            return v

        @field_validator('noise_schedule')
        def noise_schedule_validator(cls, v: str):
            if v not in ["native", "exponential", "polyexponential"]:
                raise ValueError("Invalid noise_schedule.")
            return v

        @field_validator('steps')
        def steps_validator(cls, v: int):
            if v > 28:
                logger.warning(f"steps {v} > 28, maybe charge more.")
            return v

        @field_validator('width')
        def width_validator(cls, v: int):
            """
            必须是 64 的倍数
            :param v:
            :return:
            """
            if v % 64 != 0:
                raise ValueError("Invalid width, must be multiple of 64.")
            return v

        @field_validator('height')
        def height_validator(cls, v: int):
            """
            必须是 64 的倍数
            :param v:
            :return:
            """
            if v % 64 != 0:
                raise ValueError("Invalid height, must be multiple of 64.")
            return v

        @field_validator('n_samples')
        def n_samples_validator(cls, v: int):
            """
            小于 8
            :param v:
            :return:
            """
            if v > 8:
                raise ValueError("Invalid n_samples, must be less than 8.")
            return v

    action: Optional[str] = "generate"
    input: str = "1girl, best quality, amazing quality, very aesthetic, absurdres"
    model: Optional[str] = "nai-diffusion-3"
    parameters: Params = Params()
    model_config = ConfigDict(extra="ignore")

    @property
    def base_url(self):
        return f"{self.endpoint.strip('/')}/ai/generate-image"

    @property
    def charge(self):
        return self._charge

    @charge.setter
    def charge(self, value):
        self._charge = value

    @property
    def endpoint(self):
        return self._endpoint

    @endpoint.setter
    def endpoint(self, value):
        self._endpoint = value

    @staticmethod
    def valid_wh():
        """
        宽高
        :return:
        """
        return [
            (832, 1216),
            (1216, 832),
            (1024, 1024),
        ]

    def validate_charge(self):
        if self.parameters.steps > 28 and not self.charge:
            raise CheckError("steps must be less than 28 for free users.")
        if (self.parameters.width, self.parameters.height) not in self.valid_wh() and not self.charge:
            raise CheckError("Invalid size, must be one of 832x1216, 1216x832, 1024x1024 for free users.")
        if self.parameters.n_samples != 1 and not self.charge:
            raise CheckError("n_samples must be 1 for free users.")
        return self

    @classmethod
    def build(cls,
              prompt: str,
              *,
              negative_prompt: Optional[str] = None,
              override_negative_prompt: bool = False,
              seed: int = -1,
              steps: int = 28,
              cfg_rescale: int = 0,
              sampler: str = "k_euler",
              width: int = 832,
              height: int = 1216,
              ):
        """
        正负面, step, cfg, 采样方式, seed
        :param override_negative_prompt:
        :param prompt:
        :param negative_prompt:
        :param seed:
        :param steps:
        :param cfg_rescale:
        :param sampler:
        :param width:
        :param height:
        :return: self
        """
        assert isinstance(prompt, str)
        _negative_prompt = ("nsfw, lowres, {bad}, error, fewer, extra, missing, worst quality, jpeg artifacts, "
                            "bad quality, watermark, unfinished, displeasing, chromatic aberration, signature, "
                            "extra digits, artistic error, username, scan, [abstract], bad anatomy, bad hands, "
                            "@_@, mismatched pupils, heart-shaped pupils, glowing eyes, nsfw, lowres, bad anatomy, "
                            "bad hands, text, error,missing fingers, extra digit, fewer digits, cropped,"
                            "worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, "
                            "username, blurry")
        if override_negative_prompt:
            _negative_prompt = negative_prompt
        else:
            _negative_prompt = f"{_negative_prompt}, {negative_prompt}"
        param = {
            "negative_prompt": _negative_prompt,
            "seed": seed,
            "steps": steps,
            "cfg_rescale": cfg_rescale,
            "sampler": sampler,
            "width": width,
            "height": height,
        }
        # 清理空值
        param = {k: v for k, v in param.items() if v is not None}
        return cls(
            input=prompt,
            parameters=cls.Params(**param)
        )

    async def generate(self, session: Union[AsyncSession, CurlSession]) -> NaiResult:
        if isinstance(session, CurlSession):
            session = session.session
        self.validate_charge()
        request_data = self.model_dump()
        logger.info(f"Request Data: {request_data}")
        try:
            response = await session.post(
                self.base_url,
                data=json.dumps(request_data).encode("utf-8")
            )
            if response.headers.get('Content-Type') in ['binary/octet-stream', 'application/x-zip-compressed']:
                zip_file = ZipFile(BytesIO(response.content))
                with zip_file as zf:
                    file_list = zf.namelist()
                    if not file_list:
                        raise ServerError(msg="Nai Returned zip file is empty.")
                    with zf.open(file_list[0]) as file:
                        _img = BytesIO(file.read())
            else:
                logger.error(f"response: {response.text}")
                # 解析错误内容
                try:
                    _msg = response.json()
                    message = _msg["message"]
                except Exception:
                    raise ServerError(msg=f"Unexpected content type: {response.headers.get('Content-Type')}")
                code = _msg.get("statusCode", 200)
                if message == "Error generating image":
                    raise ServerError(msg=f"[Nai Server] Generate image error: {code}")
                raise AuthError(msg=f"[Nai Server]{message}")
            try:
                _img_exif = NaiPic.read_from_img(_img)
            except Exception as e:
                logger.debug(e)
                _img_exif = NaiPic.read_from_param(prompt=self.input,
                                                   neg_prompt=self.parameters.negative_prompt,
                                                   seed=self.parameters.seed,
                                                   steps=self.parameters.steps,
                                                   cfg_rescale=self.parameters.cfg_rescale,
                                                   sampler=self.parameters.sampler,
                                                   )
            _img = _img_exif.generate_to_img_io(img_io=_img)
            _img.seek(0)
            return NaiResult(
                meta=NaiResult.RequestParams(
                    endpoint=self.base_url,
                    raw_request=request_data,
                ),
                files=(f"{str(self.input[:7])}-s{shortuuid.uuid()[:5]}.png", _img.getvalue())
            )
        except httpx.HTTPError as exc:
            raise RuntimeError(f"An HTTP error occurred: {exc}")
        except ServerError as e:
            raise e
        except Exception as e:
            raise RuntimeError(f"An error occurred: {e}")
