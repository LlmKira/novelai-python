from novelai_python._enum import TextTokenizerGroup
from novelai_python.tokenizer import NaiTokenizer

# Directly use the tokenizer!
t5_tokenizer = NaiTokenizer(TextTokenizerGroup.T5)

encoded = t5_tokenizer.encode("a fox jumped over the lazy dog")
print(encoded)
