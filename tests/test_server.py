# -*- coding: utf-8 -*-
# @Time    : 2024/1/22 下午11:50
# @Author  : sudoskys
# @File    : test_server.py


from novelai_python import GenerateImageInfer
from novelai_python.sdk.ai.generate_image import Model


def test_nai():
    try:
        gen = GenerateImageInfer.build_generate(
            prompt="1girl",
            steps=29,
            model=Model.NAI_DIFFUSION_3,
        )
        gen.validate_charge()
    except Exception as e:
        print(e)
        assert 1 == 1, e
    else:
        assert 1 == 2, "should raise error"
