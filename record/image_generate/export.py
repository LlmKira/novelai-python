import json
import pathlib
import base64
from PIL import Image
from io import BytesIO

from loguru import logger


def decode_base64_in_dict(data, current_path):
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, dict) or isinstance(v, list):
                decode_base64_in_dict(v, current_path)
            if isinstance(v, str) and len(v) > 100:
                try:
                    # Base64解码
                    image_bytes = base64.b64decode(v)
                    image = Image.open(BytesIO(image_bytes))
                except Exception as e:
                    pass
                else:
                    logger.info(f"Decoding Base64 data in {k}")
                    img_name = f"{current_path}/{k}.png"
                    image.save(img_name)
                    data[k] = 'Base64 Data'
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict) or isinstance(item, list):
                decode_base64_in_dict(item, current_path)
    return data


def handle_file(filename):
    filename_wo_ext = filename.stem
    pathlib.Path(filename_wo_ext).mkdir(parents=True, exist_ok=True)
    with open(filename, 'r') as file:
        json_data = json.load(file)
    # 取消 headers 里面 Authorization 字段，然后写回
    if 'headers' in json_data:
        if 'Authorization' in json_data['headers']:
            json_data['headers']['Authorization'] = 'Secret'
            # 写回原文件
            with open(filename, 'w') as file:
                json.dump(json_data, file, indent=2)
    request_data = json.loads(json_data.get("body", ""))
    request_data = decode_base64_in_dict(request_data, filename_wo_ext)
    # 写出包含替换字段的 JSON 文件回同名的文件夹
    with open(f"{filename_wo_ext}/{filename_wo_ext}.json", 'w') as jsonfile:
        json.dump(request_data, jsonfile, indent=2)


def main():
    # 列出当前文件夹内所有的 .json 文件
    json_files = pathlib.Path('.').glob('*.json')
    for file in json_files:
        logger.info(f"Handling {file}")
        handle_file(file)


if __name__ == "__main__":
    main()
