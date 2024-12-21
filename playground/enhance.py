# -*- coding: utf-8 -*-
# @Time    : 2024/2/13 下午1:58
# @Author  : sudoskys
# @File    : enhance.py

from loguru import logger

# NOTE About Enhance Mode
# Enhance Mode = origin model name + img2img action + width *1.5(or 1) +height *1.5(or 1) + !!diff seed!!
# :)
logger.info("\nEnhance Mode = origin model name + img2img action + width *1.5(or 1) +height *1.5(or 1) + diff seed")
logger.warning(f"\nIf you use the nai-generated image as input, please diff the seed!")
