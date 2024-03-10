# -*- coding: utf-8 -*-
import pathlib
from dataclasses import dataclass
from .cell_schema import BaseCell

_R18 = ['17.9tag']


@dataclass(frozen=True, order=True)
class R18Type(BaseCell):
    def source(self):
        data = pathlib.Path(__file__).parent.joinpath('raw/r18.json')
        return data

    TAG_17_9 = '17.9tag'
