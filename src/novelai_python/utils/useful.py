# -*- coding: utf-8 -*-
# @Time    : 2024/2/9 下午10:41
# @Author  : sudoskys
# @File    : useful.py
# @Software: PyCharm
import collections
import random
from typing import List, Union

import cv2 as cv
import numpy as np


def enum_to_list(enum_):
    return list(map(lambda x: x.value, enum_._member_map_.values()))


class QueSelect(object):
    def __init__(self, data: List[str]):
        """
        A queue selector
        :param data:
        """
        self.data = collections.deque(data)
        self.used = collections.deque()
        self.users = {}

    def get(self, user_id: Union[int, str]) -> str:
        user_id = str(user_id)
        if user_id not in self.users:
            self.users[user_id] = {'data': self.data.copy(), 'used': collections.deque()}

        user_data = self.users[user_id]['data']
        user_used = self.users[user_id]['used']

        if len(user_data) == 0:
            user_data, user_used = user_used, user_data
            # 随机掉 User data
            if len(user_data) > 2:
                random.shuffle(user_data)
            self.users[user_id]['data'] = user_data
            self.users[user_id]['used'] = user_used

        selected = user_data.popleft()
        user_used.append(selected)

        return selected


def create_mask_from_sketch(original_img_bytes: bytes,
                            sketch_img_bytes: bytes,
                            output_format: str = '.png',
                            jagged_edges: bool = True
                            ) -> bytes:
    """
    Function to create a mask from original and sketch images input as bytes. Returns bytes.

    :param jagged_edges:  Whether to create jagged edges in the mask. Defaults to False.
    :param original_img_bytes: Bytes corresponding to the original image.
    :param sketch_img_bytes: Bytes corresponding to the sketch image.
    :param output_format: Format of the output image. Defaults to '.png'. It could also be '.jpg'
    :returns bytes: Bytes corresponding to the resultant mask
    """
    # Load images
    ori_img = cv.imdecode(np.frombuffer(original_img_bytes, np.uint8), cv.IMREAD_COLOR)
    sketch_img = cv.imdecode(np.frombuffer(sketch_img_bytes, np.uint8), cv.IMREAD_COLOR)

    # Check if images have the same size
    if ori_img.shape != sketch_img.shape:
        raise ValueError("Images must have the same size.")

    # Calculate difference between the original and sketch images
    diff_img = cv.absdiff(ori_img, sketch_img)

    # Convert the difference image to grayscale
    diff_gray = cv.cvtColor(diff_img, cv.COLOR_BGR2GRAY)

    # Threshold to create the mask
    _, thresh = cv.threshold(diff_gray, 10, 255, cv.THRESH_BINARY)

    if jagged_edges:
        # Use a bigger kernel for dilation to create larger 'step' effect at the edges
        kernel = np.ones((7, 7), np.uint8)
    else:
        kernel = np.ones((3, 3), np.uint8)

    # Perform morphological opening to remove small noise
    opening = cv.morphologyEx(thresh, cv.MORPH_OPEN, kernel, iterations=2)

    # Further remove noise with a Gaussian filter
    smooth = cv.GaussianBlur(opening, (5, 5), 0)

    if jagged_edges:
        # Apply additional thresholding to create sharper, jagged edges
        _, smooth = cv.threshold(smooth, 128, 255, cv.THRESH_BINARY)

    # Convert image to BytesIO object
    is_success, buffer = cv.imencode(output_format, smooth)
    if is_success:
        output_io = buffer.tobytes()
    else:
        raise ValueError("Error during conversion of image to BytesIO object")

    return output_io
