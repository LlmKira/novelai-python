# -*- coding: utf-8 -*-
import pathlib
from dataclasses import dataclass
from .cell_schema import BaseCell

_Illustrator = ['画师']


@dataclass(frozen=True, order=True)
class IllustratorType(BaseCell):
    def source(self):
        data = pathlib.Path(__file__).parent.joinpath('raw/Illustrator.json')
        return data

    PAINTER = '画师'
