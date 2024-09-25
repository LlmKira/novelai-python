from novelai_python._enum import TextTokenizerGroup
from novelai_python.tokenizer import NaiTokenizer

tokenizer_package = NaiTokenizer("pile_tokenizer")
t_text = "Hello, World! This is a   test."
print(tokenizer_package.tokenize_text(t_text))
print(tokenizer_package.encode(t_text))
print(tokenizer_package.decode(tokenizer_package.encode(t_text)))


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
