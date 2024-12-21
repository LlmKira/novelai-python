import unittest

from novelai_python._enum import TextTokenizerGroup
from novelai_python.tokenizer import NaiTokenizer


class TestNaiTokenizer(unittest.TestCase):

    def setUp(self):
        self.text = "the quick brown fox jumps over the lazy dog"
        self.tokenizer_groups = [
            TextTokenizerGroup.CLIP,
            TextTokenizerGroup.NERDSTASH,
            TextTokenizerGroup.LLAMA3,
            TextTokenizerGroup.T5,
            TextTokenizerGroup.NAI_INLINE,
            TextTokenizerGroup.PILE_NAI,
        ]

    def test_tokenizer_encode_decode(self):
        for group in self.tokenizer_groups:
            with self.subTest(group=group):
                tokenizer = NaiTokenizer(group)
                encoded_tokens = tokenizer.encode(self.text)
                decoded_text = tokenizer.decode(encoded_tokens)
                self.assertIsInstance(encoded_tokens, list)
                self.assertIsInstance(decoded_text, str)
                self.assertEqual(decoded_text.strip(), self.text)


if __name__ == '__main__':
    unittest.main()
