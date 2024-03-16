from novelai_python.tokenizer import TokenizerUtil

tokenizer_util = TokenizerUtil(TokenizerUtil.MODEL_V2_PATH)
text = "The quick brown fox jumps over the goblin."
token_id = tokenizer_util.encode(text)
print("Token IDs:", token_id)
decoded_text = tokenizer_util.decode(token_id)
print("Decoded text:", decoded_text)
