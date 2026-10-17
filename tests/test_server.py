# @Time    : 2024/1/22 下午11:50
# @Author  : sudoskys
# @File    : test_server.py


from novelai_python import GenerateImageInfer
from novelai_python.sdk.ai.generate_image import Model


def test_more_than_28_steps_is_not_free_on_opus():
    gen = GenerateImageInfer.build_generate(prompt="1girl", steps=29, model=Model.NAI_DIFFUSION_3)
    assert gen.calculate_cost(is_opus=True) > 0
    assert (
        GenerateImageInfer.build_generate(prompt="1girl", steps=28, model=Model.NAI_DIFFUSION_3).calculate_cost(
            is_opus=True
        )
        == 0
    )
