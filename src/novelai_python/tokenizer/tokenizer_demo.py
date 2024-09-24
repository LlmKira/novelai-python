import json
import pathlib
import zlib
from typing import Dict, List

from json_repair import repair_json
from pydantic import BaseModel, model_validator
from tokenizers import Tokenizer, normalizers, pre_tokenizers, Regex, decoders
from tokenizers.models import BPE


class TokenizerSetting(BaseModel):
    class TokenizerConfig(BaseModel):
        splitRegex: str
        maxEncodeChars: int
        maxNoWhitespaceChars: int
        ignoreMerges: bool

    config: TokenizerConfig
    specialTokens: List[str]
    vocab: Dict[str, int]
    merges: list

    @model_validator(mode="after")
    def ensure(self):
        self.merges = [tuple(merge) for merge in self.merges]
        return self


# 读取和解压文件
file = pathlib.Path(__file__).parent.joinpath("llama3nai_tokenizer.def")
encoded_data = file.read_bytes()
decompress_obj = zlib.decompressobj(-zlib.MAX_WBITS)
decode = decompress_obj.decompress(encoded_data)

# 修复和解析 JSON
repaired_json = repair_json(decode.decode('utf-8'), return_objects=True)
json.dump(repaired_json, open("llama3nai_tokenizer.json", "w"), indent=4, ensure_ascii=False)
tokenizer_setting = TokenizerSetting.model_validate(repaired_json)


# 创建 tokenizer
tokenizer = Tokenizer(
    BPE(
        vocab=tokenizer_setting.vocab,
        merges=tokenizer_setting.merges,
        ignore_merges=tokenizer_setting.config.ignoreMerges
    )
)

# 设置特殊 tokens
tokenizer.add_special_tokens(tokenizer_setting.specialTokens)
# 设置截断
tokenizer.enable_truncation(max_length=tokenizer_setting.config.maxEncodeChars)
# 设置 normalizer
tokenizer.normalizer = normalizers.Sequence([
    # normalizers.NFD(),  # Decompose the Unicode characters
    # normalizers.Lowercase(),  # Convert to lowercase
    # normalizers.StripAccents()  # Remove accents
])
pre_tokenizer = pre_tokenizers.Sequence([
    pre_tokenizers.Split(
        behavior="merged_with_next",
        pattern=Regex(tokenizer_setting.config.splitRegex)
    )
])
tokenizer.pre_tokenizer = pre_tokenizer
tokenizer.decoder = decoders.BPEDecoder()

# 使用 tokenizer
text = " This"
pre_tokenized = pre_tokenizer.pre_tokenize_str(text)
print([token[0] for token in pre_tokenized])
encoded = tokenizer.encode(
    sequence=[token[0] for token in pre_tokenized],
    is_pretokenized=True,
    add_special_tokens=True
)
print(f"Encoded tokens: {encoded.tokens}")
print(f"Token IDs: {encoded.ids}")

# 解码
decoded = tokenizer.decode(encoded.ids)
print(f"Decoded text: {decoded}")
