# -*- coding: utf-8 -*-
# @Time    : 2024/1/22 下午11:50
# @Author  : sudoskys
# @File    : test_server.py
# @Software: PyCharm
from pydantic import SecretStr

from novelai_gen import NovelAiInference, CurlSession, CheckError


def test_nai():
    try:
        _nai = NovelAiInference.build(prompt="", steps=29)
        _nai.charge = False
        print(_nai.charge)
        _nai.validate_charge()
        _nai.generate(session=CurlSession(jwt_token=SecretStr("555")))
    except Exception as e:
        print(e)
        assert isinstance(e, CheckError)
    else:
        assert False
