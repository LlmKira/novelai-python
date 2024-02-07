# -*- coding: utf-8 -*-
# @Time    : 2024/2/7 下午12:14
# @Author  : sudoskys
# @File    : _shema.py
# @Software: PyCharm
from curl_cffi.requests import AsyncSession
from pydantic import BaseModel


class CredentialBase(BaseModel):
    _session: AsyncSession = None

    async def get_session(self, timeout: int = 180):
        raise NotImplementedError
