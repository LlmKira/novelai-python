import random

from novelai_python.sdk.ai.generate_image.params import Params


def test_default_seed_lower_bound_passes_validation(monkeypatch):
    monkeypatch.setattr(random, "randint", lambda low, high: low)
    params = Params()
    assert params.seed == 1
    assert Params.model_validate(params.model_dump()).seed == 1


def test_default_seed_upper_bound_passes_validation(monkeypatch):
    monkeypatch.setattr(random, "randint", lambda low, high: high)
    params = Params()
    assert Params.model_validate(params.model_dump()).seed == params.seed
