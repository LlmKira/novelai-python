# -*- coding: utf-8 -*-
# @Time    : 2024/2/7 上午11:41
# @Author  : sudoskys
# @File    : encode.py
# @Software: PyCharm
from base64 import urlsafe_b64encode
from hashlib import blake2b
from typing import Iterable, List

import argon2


# https://github.com/HanaokaYuzu/NovelAI-API/blob/master/src/novelai/utils.py#L12
def encode_access_key(username: str, password: str) -> str:
    """
    Generate hashed access key from the user's username and password using the blake2 and argon2 algorithms.
    :param username: str (plaintext)
    :param password: str (plaintext)
    :return: str
    """
    pre_salt = f"{password[:6]}{username}novelai_data_access_key"

    blake = blake2b(digest_size=16)
    blake.update(pre_salt.encode())
    salt = blake.digest()

    raw = argon2.low_level.hash_secret_raw(
        secret=password.encode(encoding="utf-8"),
        salt=salt,
        time_cost=2,
        memory_cost=int(2000000 / 1024),
        parallelism=1,
        hash_len=64,
        type=argon2.low_level.Type.ID,
    )
    hashed = urlsafe_b64encode(raw).decode()

    return hashed[:64]


import base64
import hashlib
import hmac


def sign_message(message, key):
    # 使用 HMAC 算法对消息进行哈希签名
    hmac_digest = hmac.new(key.encode(), message.encode(), hashlib.sha256).digest()
    signed_hash = base64.b64encode(hmac_digest).decode()
    return signed_hash


def encode_base64(data):
    byte_data = data.encode("UTF-8")
    encoded_data = base64.b64encode(byte_data)
    return encoded_data.decode("UTF-8")


# 解码
def decode_base64(encoded_data):
    byte_data = encoded_data.encode('UTF-8')
    decoded_data = base64.b64decode(byte_data)
    return decoded_data.decode("UTF-8")


# MIT: https://github.com/Aedial/novelai-api/blob/794c4f3d89cc86df3c7d2c401b320f1822822ac0/novelai_api/utils.py
def tokens_to_b64(tokens: Iterable[int]) -> str:
    """
    Encode a list of tokens into a base64 string that can be sent to the API
    """

    return base64.b64encode(b"".join(t.to_bytes(2, "little") for t in tokens)).decode()


# MIT:https://github.com/Aedial/novelai-api/blob/794c4f3d89cc86df3c7d2c401b320f1822822ac0/novelai_api/utils.py#L332
def b64_to_tokens(b64: str) -> List[int]:
    """
    Decode a base64 string returned by the API into a list of tokens
    """

    b = base64.b64decode(b64)

    return [int.from_bytes(b[i: i + 2], "little") for i in range(0, len(b), 2)]
