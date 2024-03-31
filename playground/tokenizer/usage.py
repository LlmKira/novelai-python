from novelai_python.tokenizer import TokenizerUtil

tokenizer_util = TokenizerUtil(TokenizerUtil.MODEL_V2_PATH)
text = "The quick brown fox jumps over the goblin."
token_id = tokenizer_util.encode(text)
print("Token IDs:", token_id)
decoded_text = tokenizer_util.decode(token_id)
print("Decoded text:", decoded_text)


def limit_prompt_shown(raw_text: str, token_limit=225):
    assert isinstance(raw_text, str), "raw_text must be a string"
    tokenizer = TokenizerUtil(TokenizerUtil.MODEL_V2_PATH)
    token_array = tokenizer.encode(raw_text)
    used_tokens_len = len(token_array)
    if used_tokens_len > token_limit:
        clipped_text = tokenizer.decode(token_array[:token_limit])
        return f"{clipped_text}...{used_tokens_len}/{token_limit}"
    else:
        return f"{raw_text}"


raw_text = "The quick brown fox jumps over the goblin."
print(limit_prompt_shown(raw_text, 5))
