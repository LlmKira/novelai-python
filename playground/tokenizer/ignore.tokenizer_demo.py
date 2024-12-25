import json
import os
import pathlib
import zlib
from typing import Dict, List, Optional

import requests
from json_repair import repair_json
from pydantic import BaseModel, model_validator
from tokenizers import Tokenizer, pre_tokenizers, Regex, decoders
from tokenizers.models import BPE

# https://novelai.net/tokenizer/compressed/llama3nai_tokenizer.def?v=2&static=true

model_name = "clip_tokenizer"
model_full_name = f"{model_name}.def"
url = f"https://novelai.net/tokenizer/compressed/{model_full_name}?v=2&static=true"
if not os.path.exists(model_full_name):
    print(f"Downloading {model_full_name} from {url}")
    response = requests.get(url)
    response.raise_for_status()
    # write down
    with open(model_full_name, "wb") as f:
        f.write(response.content)


class TokenizerSetting(BaseModel):
    class TokenizerConfig(BaseModel):
        splitRegex: str
        maxEncodeChars: Optional[int] = None
        maxNoWhitespaceChars: Optional[int] = None
        ignoreMerges: Optional[bool] = False

    config: TokenizerConfig
    specialTokens: List[str]
    vocab: Dict[str, int]
    merges: list

    @model_validator(mode="after")
    def ensure(self):
        self.merges = [tuple(merge) for merge in self.merges]
        return self


# 读取和解压文件
file = pathlib.Path(__file__).parent.joinpath(model_full_name)
encoded_data = file.read_bytes()
decompress_obj = zlib.decompressobj(-zlib.MAX_WBITS)
decode = decompress_obj.decompress(encoded_data)

# 修复和解析 JSON
repaired_json = repair_json(decode.decode('utf-8'), return_objects=True)
json.dump(repaired_json, open(f"{model_name}.json", "w"), indent=2)
tokenizer_setting = TokenizerSetting.model_validate(repaired_json)

# 创建 tokenizer
tokenizer = Tokenizer(BPE(
    vocab=tokenizer_setting.vocab,
    merges=tokenizer_setting.merges,
    ignore_merges=tokenizer_setting.config.ignoreMerges
))

# 设置特殊 tokens
tokenizer.add_special_tokens(tokenizer_setting.specialTokens)
print(tokenizer.token_to_id(" "))
if tokenizer_setting.config.maxEncodeChars:
    tokenizer.enable_truncation(max_length=tokenizer_setting.config.maxEncodeChars)
# 设置 normalizer
# tokenizer.normalizer = normalizers.Sequence([])

# 设置 pre_tokenizer
pre_zus = [
    pre_tokenizers.Split(
        behavior="merged_with_next",
        pattern=Regex(tokenizer_setting.config.splitRegex)
    ),
]
if tokenizer.token_to_id(" ") is None:
    pre_zus.append(pre_tokenizers.ByteLevel(add_prefix_space=False, use_regex=False))
pre_tokenizer = pre_tokenizers.Sequence(pre_zus)

tokenizer.pre_tokenizer = pre_tokenizer
tokenizer.decoder = decoders.ByteLevel()

# 使用 tokenizer
text = "Hello, World! This is a test."
encoded = tokenizer.encode(text, add_special_tokens=True)
print(f"Pre-tokenized text: {pre_tokenizer.pre_tokenize_str(text)}")
print(f"Encoded tokens: {encoded.tokens}")
print(f"Token IDs: {encoded.ids}")

# 解码
decoded = tokenizer.decode(encoded.ids)
print(f"Decoded text:{decoded}")
