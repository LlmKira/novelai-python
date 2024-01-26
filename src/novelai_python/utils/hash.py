# -*- coding: utf-8 -*-
# @Time    : 2024/1/23 上午9:22
# @Author  : sudoskys
# @File    : hash.py
# @Software: PyCharm
import base64
import hashlib
import hmac
import json
from io import BytesIO
from typing import Union

from PIL import Image
from PIL.PngImagePlugin import PngInfo
from loguru import logger
from pydantic import BaseModel


def sign_message(message, key):
    # 使用 HMAC 算法对消息进行哈希签名
    hmac_digest = hmac.new(key.encode(), message.encode(), hashlib.sha256).digest()
    signed_hash = base64.b64encode(hmac_digest).decode()
    return signed_hash


class NovelAiMetadata(BaseModel):
    title: str = "AI generated image"
    description: str
    comment: Union[dict, str] = {}

    @property
    def metadata(self):
        if isinstance(self.comment, dict):
            _comment = json.dumps(self.comment)
        return {"Title": self.title, "Description": self.description, "Comment": self.comment}

    @staticmethod
    def rehash(img_io):
        cls = NaiPic.read_from_img(img_io)
        cls.comment["signed_hash"] = sign_message(json.dumps(cls.description), "novalai-client")
        cls.write_out(img_io=img_io)
        return img_io

    def write_out(self, img_io: BytesIO):
        with Image.open(img_io) as img:
            metadata = PngInfo()
            for k, v in self.metadata.items():
                metadata.add_text(k, v)
            _new_img = BytesIO()
            img.save(_new_img, format="PNG", pnginfo=metadata, quality=95, optimize=False)
        return _new_img

    @classmethod
    def build_from_img(cls, image_io):
        with Image.open(image_io) as img:
            title = img.info.get("Title")
            if not title == 'AI generated image':
                raise ValueError("Not a NaiPic")
            prompt = img.info.get("Description")
            comment = img.info.get("Comment")
            try:
                comment = json.loads(comment)
            except Exception as e:
                logger.debug(e)
                comment = {}
            return cls(title=title, description=prompt, comment=comment)

    @classmethod
    def build_from_param(cls, prompt, neg_prompt, **kwargs):
        _comment = {"uc": neg_prompt}
        _comment.update(kwargs)
        return cls(title="AI generated image", description=prompt, comment=_comment)


# 编码
def encode_base64(data):
    # 使用UTF-8将字符串转为字节对象
    byte_data = data.encode("UTF-8")
    # 使用base64编码
    encoded_data = base64.b64encode(byte_data)
    return encoded_data.decode("UTF-8")  # 再次使用UTF-8将字节对象转为字符串


# 解码
def decode_base64(encoded_data):
    # 使用UTF-8将字符串转为字节对象
    byte_data = encoded_data.encode('UTF-8')
    # 使用base64解码
    decoded_data = base64.b64decode(byte_data)
    return decoded_data.decode("UTF-8")  # 再次使用UTF-8将字节对象转为字符串
