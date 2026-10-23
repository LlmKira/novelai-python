import json
import pathlib
import unittest
import zlib

import pytest

from novelai_python._enum import TextTokenizerGroup
from novelai_python.tokenizer import NaiTokenizer
from novelai_python.tokenizer.clip_tokenizer import bytes_to_unicode

# Recorded with 0.8.1, which ran on HF tokenizers: the kitoken definitions must reproduce it.
GOLDEN = json.loads((pathlib.Path(__file__).parent / "fixtures" / "tokenizer_golden.json").read_text(encoding="utf-8"))


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


@pytest.mark.network  # tokenizer files are downloaded on first use
@pytest.mark.parametrize("group", sorted(GOLDEN["groups"]))
def test_outputs_match_tokenizers_implementation(group):
    expected = GOLDEN["groups"][group]
    tokenizer = NaiTokenizer(group)
    assert tokenizer.total_tokens() == expected["vocab_size"]
    assert [tokenizer.encode(t) for t in GOLDEN["texts"]] == expected["ids"]
    tokens = [tokenizer.tokenize_text(t) for t in GOLDEN["texts"][:6]]
    if group == "t5_tokenizer":
        # tokenizers showed the source text of a piece T5 cannot encode; kitoken has no offsets, so it is <unk>
        tokens = [
            [want if got == "<unk>" else got for got, want in zip(row, wanted, strict=True)]
            for row, wanted in zip(tokens, expected["tokens"], strict=True)
        ]
    assert tokens == expected["tokens"]
    for ids, decoded in zip(expected["ids"], expected["decoded"], strict=True):
        if group == "nerdstash_tokenizer" and "�" in decoded:
            continue  # 0.8.1 garbled non-ASCII here, see test_nerdstash_decodes_non_ascii
        assert tokenizer.decode(ids) == decoded


@pytest.mark.network
def test_nerdstash_decodes_non_ascii():
    tokenizer = NaiTokenizer(TextTokenizerGroup.NERDSTASH)
    assert tokenizer.decode(tokenizer.encode("café, ёжик")) == "café, ёжик"


def write_def(directory: pathlib.Path, name: str, data) -> None:
    raw = data if isinstance(data, str) else json.dumps(data)
    (directory / f"{name}.def").write_bytes(zlib.compress(raw.encode("utf-8")))


class NoDownload:
    def get(self, *args, **kwargs):
        raise AssertionError("the .def file is on disk, nothing to download")


def test_byte_level_bpe_from_def(tmp_path):
    byte_chars = list(bytes_to_unicode().values())
    merges = [("h", "e"), ("l", "l"), ("he", "ll"), ("hell", "o")]
    vocab = {c: i for i, c in enumerate(byte_chars)} | {"".join(m): 256 + i for i, m in enumerate(merges)}
    write_def(
        tmp_path,
        "gpt2_tokenizer",
        {
            "config": {"splitRegex": r"'s|'t|'re|'ve|'m|'ll|'d| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"},
            "specialTokens": ["<|endoftext|>"],
            "vocab": vocab,
            "merges": merges,
        },
    )
    tokenizer = NaiTokenizer("gpt2_tokenizer", tokenizer_model_path=tmp_path, download_session=NoDownload())
    endoftext = len(vocab)  # a special token outside the vocabulary gets the next id
    assert tokenizer.encode("hello<|endoftext|>") == [vocab["hello"], endoftext]
    assert tokenizer.total_tokens() == len(vocab) + 1
    assert tokenizer.tokenize_text(" hello") == [" ", "hello"]
    assert tokenizer.decode(tokenizer.encode("héllo wörld")) == "héllo wörld"


def test_char_level_bpe_decodes_non_ascii(tmp_path):
    # a vocabulary with a plain space is not byte-level (nerdstash); 0.8.1 decoded café as caf�
    vocab = {" ": 0, "c": 1, "a": 2, "f": 3, "é": 4, "1": 5, "ca": 6, "caf": 7, "café": 8}
    write_def(
        tmp_path,
        "nerdstash_tokenizer",
        {
            "config": {"splitRegex": r" ?\p{L}+| ?\d+| ?[^\t\n\f\r \p{L}\d]+|[\t\n\f\r ]+"},
            "specialTokens": ["1"],
            "vocab": vocab,
            "merges": [("c", "a"), ("ca", "f"), ("caf", "é")],
        },
    )
    tokenizer = NaiTokenizer("nerdstash_tokenizer", tokenizer_model_path=tmp_path, download_session=NoDownload())
    assert tokenizer.encode("café 1") == [8, 0, 5]
    assert tokenizer.decode([8]) == "café"


def test_t5_appends_the_template_end_token(tmp_path):
    def special(token_id, content):
        return {"id": token_id, "content": content, "single_word": False, "lstrip": False, "rstrip": False,
                "normalized": False, "special": True}  # fmt: skip

    metaspace = {"type": "Metaspace", "replacement": "▁", "prepend_scheme": "always", "split": True}
    end = {"SpecialToken": {"id": "</s>", "type_id": 0}}
    definition = {
        "version": "1.0",
        "truncation": None,
        "padding": None,
        "added_tokens": [special(0, "<pad>"), special(1, "</s>"), special(2, "<unk>")],
        "normalizer": None,
        "pre_tokenizer": metaspace,
        "post_processor": {
            "type": "TemplateProcessing",
            "single": [{"Sequence": {"id": "A", "type_id": 0}}, end],
            "pair": [{"Sequence": {"id": "A", "type_id": 0}}, end, {"Sequence": {"id": "B", "type_id": 0}}, end],
            "special_tokens": {"</s>": {"id": "</s>", "ids": [1], "tokens": ["</s>"]}},
        },
        "decoder": metaspace,
        "model": {
            "type": "Unigram",
            "unk_id": 2,
            "vocab": [["<pad>", 0.0], ["</s>", 0.0], ["<unk>", 0.0], ["▁", -2.0], ["▁hello", -1.0], ["▁world", -1.0]],
            "byte_fallback": False,
        },
    }
    write_def(tmp_path, "t5_tokenizer", json.dumps(definition))
    tokenizer = NaiTokenizer("t5_tokenizer", tokenizer_model_path=tmp_path, download_session=NoDownload())
    assert tokenizer.encode("hello world") == [4, 5, 1]
    assert tokenizer.tokenize_text("hello world") == ["▁hello", "▁world", "</s>"]
    assert tokenizer.decode([4, 5, 1]) == "hello world"
    assert tokenizer.total_tokens() == 6


def test_clip_from_def(tmp_path):
    write_def(tmp_path, "clip_tokenizer", {"text": "#version: 0.2\nh e\nl l\nhe ll\nhell o</w>"})
    tokenizer = NaiTokenizer("clip_tokenizer", tokenizer_model_path=tmp_path, download_session=NoDownload())
    hello = 512 + 3  # 256 byte tokens, 256 end-of-word ones, then the merges in order
    assert tokenizer.encode("  HELLO ") == [hello]
    assert tokenizer.tokenize_text("Hello") == ["hello "]
    assert tokenizer.decode([hello, hello]) == "hello hello "
    assert tokenizer.total_tokens() == 512 + 4 + 2


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
    assert target.stat().st_mode & 0o777 == 0o644
    assert not list(tmp_path.glob(".*.tmp"))


def test_truncated_cache_is_downloaded_again(tmp_path):
    import json
    import zlib

    full = json.dumps({"text": "x"}).encode()
    compressed = zlib.compress(full)
    (tmp_path / "clip_tokenizer.def").write_bytes(zlib.compress(full[:-3]))  # cut-off JSON, valid zlib

    class Response:
        content = compressed

        def raise_for_status(self) -> None:
            pass

    class Session:
        calls = 0

        def get(self, *args, **kwargs):
            Session.calls += 1
            return Response()

    tokenizer = NaiTokenizer.__new__(NaiTokenizer)
    tokenizer.model_full_name = "clip_tokenizer.def"
    tokenizer.tokenizer_model_path = tmp_path
    tokenizer._download_session = Session()
    tokenizer._load_tokenizer_settings()
    assert Session.calls == 1
    assert (tmp_path / "clip_tokenizer.def").read_bytes() == compressed


if __name__ == "__main__":
    unittest.main()
