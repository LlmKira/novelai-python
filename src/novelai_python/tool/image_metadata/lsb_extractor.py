# MIT: https://github.com/NovelAI/novelai-image-metadata/blob/main/nai_meta.py
from io import BytesIO
from pathlib import Path
from typing import Union

from PIL import Image
import numpy as np
import gzip
import json


class LSBExtractor(object):
    def __init__(self, data):
        self.data = data
        self.rows, self.cols, self.dim = data.shape
        self.bits = 0
        self.byte = 0
        self.row = 0
        self.col = 0

    def _extract_next_bit(self):
        if self.row < self.rows and self.col < self.cols:
            bit = self.data[self.row, self.col, self.dim - 1] & 1
            self.bits += 1
            self.byte <<= 1
            self.byte |= bit
            self.row += 1
            if self.row == self.rows:
                self.row = 0
                self.col += 1

    def get_one_byte(self):
        while self.bits < 8:
            self._extract_next_bit()
        byte = bytearray([self.byte])
        self.bits = 0
        self.byte = 0
        return byte

    def get_next_n_bytes(self, n):
        bytes_list = bytearray()
        for _ in range(n):
            byte = self.get_one_byte()
            if not byte:
                break
            bytes_list.extend(byte)
        return bytes_list

    def read_32bit_integer(self):
        bytes_list = self.get_next_n_bytes(4)
        if len(bytes_list) == 4:
            integer_value = int.from_bytes(bytes_list, byteorder='big')
            return integer_value
        else:
            return None


class ImageLsbDataExtractor(object):
    def __init__(self):
        self.magic = "stealth_pngcomp"

    def extract_data(self, image: Union[str, bytes, Path, BytesIO, np.ndarray]) -> dict:
        try:
            if isinstance(image, Image.Image):
                image = np.array(image)
            elif isinstance(image, (str, bytes, Path, BytesIO)):
                img = Image.open(image)
                image = np.array(img)

            if not (image.shape[-1] == 4 and len(image.shape) == 3):
                raise AssertionError('image format error')

            reader = LSBExtractor(image)

            read_magic = reader.get_next_n_bytes(len(self.magic)).decode("utf-8")
            if not (self.magic == read_magic):
                raise AssertionError('magic number mismatch')

            read_len = reader.read_32bit_integer() // 8
            json_data = reader.get_next_n_bytes(read_len)

            json_data = json.loads(gzip.decompress(json_data).decode("utf-8"))
            if "Comment" in json_data:
                json_data["Comment"] = json.loads(json_data["Comment"])
            return json_data
        except FileNotFoundError:
            # 无法找到文件
            raise Exception(f"The file {image} does not exist.")

        except json.JSONDecodeError as e:
            # 无法解析JSON数据
            raise Exception(f"Failed to decode JSON data from image: {image}. Error: {str(e)}")

        except AssertionError as err:
            # 魔数不匹配
            raise Exception(f"Failed to extract data from image: {image}. Error: {str(err)}")

        except Exception as e:
            # 从图像中提取数据时发生意外错误
            raise Exception(f"Unexpected error happened when extracting data from image: {image}. Error: {str(e)}")
