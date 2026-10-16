# @Time    : 2024/2/7 上午11:41
import base64
import hashlib
import hmac
from base64 import urlsafe_b64encode
from hashlib import blake2b

import numpy as np
from nacl.pwhash import argon2id


# https://github.com/HanaokaYuzu/NovelAI-API/blob/master/src/novelai/utils.py#L12
def encode_access_key(username: str, password: str) -> str:
    """
    Generate hashed access key from the user's username and password using the blake2 and argon2 algorithms.
    :param username: str (plaintext)
    :param password: str (plaintext)
    :return: str
    """
    pre_salt = f"{password[:6]}{username.lower()}novelai_data_access_key"

    blake = blake2b(digest_size=16)
    blake.update(pre_salt.encode())
    salt = blake.digest()

    # libsodium argon2id (single lane, like the web client's parallelism=1);
    # memlimit is in bytes: 2_000_000 / 1024 KiB rounded down, as argon2-cffi did.
    raw = argon2id.kdf(
        64,
        password.encode(encoding="utf-8"),
        salt,
        opslimit=2,
        memlimit=(2_000_000 // 1024) * 1024,
    )
    hashed = urlsafe_b64encode(raw).decode()

    return hashed[:64]


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
    byte_data = encoded_data.encode("UTF-8")
    decoded_data = base64.b64decode(byte_data)
    return decoded_data.decode("UTF-8")


def b64_to_tokens(encoded_str, dtype="uint32"):
    """
    big-endian
    将 Base64 编码的字符串解码为 tokens 数组。
    :param encoded_str: 从 Base64 解码的字符串
    :param dtype: 解码的数组类型，可以是 'uint32' 或 'uint16'
    :return: 解码后的整数数组
    """
    # NOTE:
    byte_data = base64.b64decode(encoded_str)
    if dtype == "uint32":
        array_data = np.frombuffer(byte_data, dtype=np.uint32)
    elif dtype == "uint16":
        array_data = np.frombuffer(byte_data, dtype=np.uint16)
    else:
        raise ValueError("Unsupported dtype")
    return array_data.tolist()


def tokens_to_b64(tokens, dtype="uint32"):
    """
    big-endian
    将给定的 token 数组编码为 Base64 字符串。
    :param tokens: 输入的整数数组
    :param dtype: 输出的数组类型，可以是 'uint32' 或 'uint16'
    :return: base64 编码字符串
    """
    # 根据 dtype 确定 numpy 数组数据类型
    if dtype == "uint32":
        array_data = np.array(tokens, dtype=np.uint32)
    elif dtype == "uint16":
        array_data = np.array(tokens, dtype=np.uint16)
    else:
        raise ValueError("Unsupported dtype")
    byte_data = array_data.tobytes()
    base64_str = base64.b64encode(byte_data).decode("utf-8")
    return base64_str
