import unittest

import pytest

from novelai_python._enum import TextTokenizerGroup
from novelai_python.tokenizer import NaiTokenizer


@pytest.mark.network  # tokenizer files are downloaded on first use
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


def test_tokenizer_dir_override(monkeypatch, tmp_path):
    from novelai_python.tokenizer import default_tokenizer_dir

    target = tmp_path / "tok"
    monkeypatch.setenv("NOVELAI_TOKENIZER_DIR", str(target))
    assert default_tokenizer_dir() == target
    assert target.is_dir()


def test_download_file_is_atomic(tmp_path):
    from novelai_python.tokenizer import download_file

    class Response:
        content = b"tokenizer"

        def raise_for_status(self) -> None:
            pass

    class Session:
        def get(self, *args, **kwargs):
            return Response()

    target = tmp_path / "clip_tokenizer.def"
    download_file("https://example.invalid/x", target, Session())
    assert target.read_bytes() == b"tokenizer"
    assert not list(tmp_path.glob(".*.tmp"))


if __name__ == "__main__":
    unittest.main()
