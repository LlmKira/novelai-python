# -*- coding: utf-8 -*-
# @Time    : 2024/2/7 上午11:41
# @Author  : sudoskys
# @File    : encode.py
# @Software: PyCharm
from base64 import urlsafe_b64encode
from hashlib import blake2b

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
