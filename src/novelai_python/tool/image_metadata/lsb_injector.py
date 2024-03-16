# MIT: https://github.com/NovelAI/novelai-image-metadata/blob/main/nai_meta_writer.py
import json
import gzip
import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo


class LSBInjector:
    def __init__(self, data):
        self.data = data
        self.rows, self.cols, self.dim = data.shape
        self.bits = 0
        self.byte = 0
        self.row = 0
        self.col = 0

    def put_byte(self, byte):
        for i in range(8):
            bit = (byte & 0x80) >> 7
            self.data[self.row, self.col, self.dim - 1] &= 0xfe
            self.data[self.row, self.col, self.dim - 1] |= bit
            self.row += 1
            if self.row == self.rows:
                self.row = 0
                self.col += 1
                assert self.col < self.cols
            byte <<= 1

    def put_32bit_integer(self, integer_value):
        bytes_list = integer_value.to_bytes(4, byteorder='big')
        for byte in bytes_list:
            self.put_byte(byte)

    def put_bytes(self, bytes_list):
        for byte in bytes_list:
            self.put_byte(byte)

    def put_string(self, string):
        self.put_bytes(string.encode('utf-8'))


def serialize_metadata(metadata: PngInfo) -> bytes:
    # Extract metadata from PNG chunks
    data = {
        k: v
        for k, v in [
            data[1]
            .decode("latin-1" if data[0] == b"tEXt" else "utf-8")
            .split("\x00" if data[0] == b"tEXt" else "\x00\x00\x00\x00\x00")
            for data in metadata.chunks
            if data[0] == b"tEXt" or data[0] == b"iTXt"
        ]
    }
    # Save space by getting rid of reduntant metadata (Title is static)
    if "Title" in data:
        del data["Title"]
    # Encode and compress data using gzip
    data_encoded = json.dumps(data)
    return gzip.compress(bytes(data_encoded, "utf-8"))


def inject_data(image: Image.Image, data: PngInfo) -> Image.Image:
    image = image.convert('RGBA')
    pixels = np.array(image)
    injector = LSBInjector(pixels)
    injector.put_string("stealth_pngcomp")
    data = serialize_metadata(data)
    injector.put_32bit_integer(len(data) * 8)
    injector.put_bytes(data)
    return Image.fromarray(injector.data)
