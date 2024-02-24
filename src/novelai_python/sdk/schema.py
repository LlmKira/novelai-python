# -*- coding: utf-8 -*-
# @Time    : 2024/2/10 上午11:15
# @Author  : sudoskys
# @File    : schema.py
# @Software: PyCharm
from abc import ABC, abstractmethod
from typing import Optional, Union

from curl_cffi.requests import AsyncSession
from pydantic import BaseModel, PrivateAttr

from ..credential import CredentialBase


class ApiBaseModel(BaseModel, ABC):
    _endpoint: Optional[str] = PrivateAttr()

    @property
    def endpoint(self):
        return self._endpoint

    @endpoint.setter
    def endpoint(self, value):
        self._endpoint = value

    @abstractmethod
    async def necessary_headers(self, request_data) -> dict:
        raise NotImplementedError()

    @abstractmethod
    async def request(self,
                      session: Union[AsyncSession, CredentialBase],
                      *,
                      override_headers: Optional[dict] = None
                      ):
        raise NotImplementedError()
