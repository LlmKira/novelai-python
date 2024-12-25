# MIT: https://github.com/NovelAI/novelai-image-metadata/blob/main/nai_meta.py
import gzip
import json

import numpy as np
from PIL import Image


class LSBExtractor(object):
    def __init__(self, data):
        self.data = data
        self.rows, self.cols, self.dim = data.shape
        self.bits = 0
        self.byte = 0
        self.row = 0
        self.col = 0

    def _extract_next_bit(self):
        """
        Extract the next bit from the pixel's least significant bit (LSB).
        Returns `True` if a bit was successfully extracted, `False`
        if we have reached the end of the data.
        """
        if self.row < self.rows and self.col < self.cols:
            bit = self.data[self.row, self.col, self.dim - 1] & 1
            self.bits += 1
            self.byte <<= 1
            self.byte |= bit
            self.row += 1
            if self.row == self.rows:
                self.row = 0
                self.col += 1
            return True
        return False

    def get_one_byte(self):
        """
        Extract one byte (8 bits) from the image data using LSB.
        Returns the byte if successfully extracted, otherwise `None` if the data ends prematurely.
        """
        while self.bits < 8:
            if not self._extract_next_bit():
                # If we run out of data before completing a byte, return None
                if self.bits == 0:
                    return None

                # If we have partial bits, pad remaining bits with 0s and return
                self.byte <<= (8 - self.bits)
                padded_byte = bytearray([self.byte])
                self.bits = 0
                self.byte = 0
                return padded_byte

        byte = bytearray([self.byte])
        self.bits = 0
        self.byte = 0
        return byte

    def get_next_n_bytes(self, n):
        """
        Extract the next `n` bytes sequentially from the image data.
        Stops if not enough data is available.
        """
        bytes_list = bytearray()
        for _ in range(n):
            byte = self.get_one_byte()
            if byte is None:  # Stop if we run out of data
                break
            bytes_list.extend(byte)
        return bytes_list

    def read_32bit_integer(self):
        """
        Attempt to read a 32-bit integer (4 bytes).
        Returns the integer value if successfully extracted, otherwise `None`
        if insufficient data is available.
        """
        bytes_list = self.get_next_n_bytes(4)
        if len(bytes_list) == 4:
            integer_value = int.from_bytes(bytes_list, byteorder='big')
            return integer_value
        else:
            return None


class ImageLsbDataExtractor(object):
    def __init__(self):
        self.magic = "stealth_pngcomp"

    def extract_data(self, image: Image.Image, get_fec: bool = False) -> tuple:
        """
        Get the data from the image
        :param image: Pillow Image object
        :param get_fec: bool
        :return: json_data, fec_data
        """
        image = np.array(image.copy().convert("RGBA"))
        try:
            if not (image.shape[-1] == 4 and len(image.shape) == 3):
                raise AssertionError('image format error, maybe image already be modified')
            reader = LSBExtractor(image)
            read_magic = reader.get_next_n_bytes(len(self.magic)).decode("utf-8")
            if not (self.magic == read_magic):
                raise AssertionError('magic number mismatch')
            read_len = reader.read_32bit_integer() // 8
            json_data = reader.get_next_n_bytes(read_len)
            json_data = json.loads(gzip.decompress(json_data).decode("utf-8"))
            if "Comment" in json_data:
                json_data["Comment"] = json.loads(json_data["Comment"])

            if not get_fec:
                return json_data, None

            fec_len = reader.read_32bit_integer()
            fec_data = None
            if fec_len != 0xffffffff:
                fec_data = reader.get_next_n_bytes(fec_len // 8)

            return json_data, fec_data
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
