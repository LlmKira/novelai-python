from novelai_python._enum import get_tokenizer_model, TextLLMModel, TextTokenizerGroup
from novelai_python.tokenizer import NaiTokenizer
from novelai_python.utils.encode import b64_to_tokens

# !Through llm model name to get the tokenizer
tokenizer_package = NaiTokenizer(get_tokenizer_model(TextLLMModel.ERATO))

# Directly use the tokenizer!
clip_tokenizer = NaiTokenizer(TextTokenizerGroup.CLIP)

t_text = "a fox jumped over the lazy dog"
encode_tokens = tokenizer_package.encode(t_text)
print(tokenizer_package.tokenize_text(t_text))
print(f"Tokenized text: {encode_tokens}")
print(tokenizer_package.decode(tokenizer_package.encode(t_text)))

b64 = "UfQBADoAAABIAQAAGQAAANwAAAATAAAAexQAAEAAAAD/mwAA2GkAAJ8DAAAXAQAAtT4AAC8WAAA="
oks = b64_to_tokens(b64)
print(oks)


def limit_prompt_shown(raw_text: str, token_limit=225):
    assert isinstance(raw_text, str), "raw_text must be a string"
    tokenizer = NaiTokenizer(TextTokenizerGroup.NERDSTASH_V2)
    token_array = tokenizer.encode(raw_text)
    used_tokens_len = len(token_array)
    if used_tokens_len > token_limit:
        clipped_text = tokenizer.decode(token_array[:token_limit])
        return f"{clipped_text}...{used_tokens_len}/{token_limit}"
    else:
        return f"{raw_text}"


raw_text = "The quick brown fox jumps over the goblin."
print(limit_prompt_shown(raw_text, 5))
