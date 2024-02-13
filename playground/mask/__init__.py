# -*- coding: utf-8 -*-
# @Time    : 2024/2/13 下午12:42
# @Author  : sudoskys
# @File    : __init__.py.py
# @Software: PyCharm
from novelai_python.utils.useful import create_mask_from_sketch

with open('sk2.jpg', 'rb') as f:
    sk_bytes = f.read()

with open('ori2.png', 'rb') as f:
    ori_bytes = f.read()

return_bytes = create_mask_from_sketch(original_img_bytes=ori_bytes,
                                       sketch_img_bytes=sk_bytes,
                                       jagged_edges=True,
                                       min_block_size=15
                                       )

with open('mask_export.png', 'wb') as f:
    f.write(return_bytes)
