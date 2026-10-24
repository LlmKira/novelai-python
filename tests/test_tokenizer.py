import json
import pathlib
import unittest
import zlib

import pytest

from novelai_python._enum import TextTokenizerGroup
from novelai_python.tokenizer import NaiTokenizer
from novelai_python.tokenizer._definition import js_regex
from novelai_python.tokenizer.clip_tokenizer import bytes_to_unicode

# "groups": CLIP and T5 as recorded with 0.8.1, which ran on HF tokenizers. "site_groups": the BPE
# tokenizers as the site's own tokenizer (the class in the novelai.net bundle, run in Node) encodes and
# decodes "site_texts"; decoded with control markers like <|endoftext|> taken out first.
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
        assert tokenizer.decode(ids) == decoded


@pytest.mark.network  # tokenizer files are downloaded on first use
@pytest.mark.parametrize("group", sorted(GOLDEN["site_groups"]))
def test_outputs_match_the_site(group):
    expected = GOLDEN["site_groups"][group]
    tokenizer = NaiTokenizer(group)
    assert tokenizer.total_tokens() == expected["vocab_size"]
    assert [tokenizer.encode(t) for t in GOLDEN["site_texts"]] == expected["ids"]
    assert [tokenizer.decode(ids) for ids in expected["ids"]] == expected["decoded"]


@pytest.mark.network
def test_nerdstash_keeps_newlines_digits_and_non_ascii():
    for group in (TextTokenizerGroup.NERDSTASH, TextTokenizerGroup.NERDSTASH_V2):
        tokenizer = NaiTokenizer(group)
        text = "The year was 1999.\n\tcafé, ёжик 🙂"
        assert tokenizer.decode(tokenizer.encode(text)) == text


def write_def(directory: pathlib.Path, name: str, data) -> None:
    raw = data if isinstance(data, str) else json.dumps(data)
    (directory / f"{name}.def").write_bytes(zlib.compress(raw.encode("utf-8")))


class NoDownload:
    def get(self, *args, **kwargs):
        raise AssertionError("the .def file is on disk, nothing to download")


GPT2_SPLIT = r"'s|'t|'re|'ve|'m|'ll|'d| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"


def byte_level_def(tmp_path, merges, extra=(), specials=(), **config):
    vocab = {c: i for i, c in enumerate(bytes_to_unicode().values())}
    for token in ["".join(m) for m in merges] + list(extra) + list(specials):
        vocab.setdefault(token, len(vocab))
    listed = [*specials, "<|missing|>"]  # listed as special but not in the vocabulary: the site ignores it
    write_def(
        tmp_path,
        "gpt2_tokenizer",
        {"config": {"splitRegex": GPT2_SPLIT, **config}, "specialTokens": listed, "vocab": vocab, "merges": merges},
    )
    return vocab, NaiTokenizer("gpt2_tokenizer", tokenizer_model_path=tmp_path, download_session=NoDownload())


def test_byte_level_bpe_from_def(tmp_path):
    merges = [("h", "e"), ("l", "l"), ("he", "ll"), ("hell", "o")]
    vocab, tokenizer = byte_level_def(tmp_path, merges, specials=["<|endoftext|>"])
    assert tokenizer.encode("hello<|endoftext|>") == [vocab["hello"], vocab["<|endoftext|>"]]
    assert len(tokenizer.encode("<|missing|>")) > 1  # plain text
    assert tokenizer.total_tokens() == len(vocab)
    assert tokenizer.tokenize_text(" hello") == [" ", "hello"]
    assert tokenizer.decode(tokenizer.encode("héllo wörld<|endoftext|>")) == "héllo wörld"  # control marker dropped


def test_tokens_no_merge_produces_are_not_used(tmp_path):
    # genji has 4277 such tokens; the site builds words from the merge list only
    vocab, tokenizer = byte_level_def(tmp_path, [("h", "e"), ("l", "l"), ("he", "ll")], extra=["hello"])
    assert tokenizer.encode("hello") == [vocab["hell"], vocab["o"]]


def test_long_text_is_encoded_in_pieces_of_max_encode_chars(tmp_path):
    vocab, tokenizer = byte_level_def(tmp_path, [("a", "a")], maxEncodeChars=3)
    assert tokenizer.encode("aaaaa") == [vocab["aa"], vocab["a"], vocab["aa"]]  # "aaa" + "aa", not "aa aa a"


def test_split_regex_classes_read_as_in_javascript():
    space = r"\t\n\x0B\f\r \u00A0\u1680\u2000-\u200A\u2028\u2029\u202F\u205F\u3000\uFEFF"
    assert js_regex(r"\s+(?!\S)|[^\s\p{L}]| ?\d+") == rf"[{space}]+(?![^{space}])|[^{space}\p{{L}}]| ?[0-9]+"
    assert js_regex(r"\\s") == r"\\s"  # an escaped backslash is left alone


def test_char_level_bpe_falls_back_to_byte_tokens(tmp_path):
    # nerdstash: characters plus byte tokens 0x00-0xff; what has no token goes out as its UTF-8 bytes
    vocab = {f"0x{b:02x}": b for b in range(256)}
    for token in [" ", "c", "a", "f", "é", "1", "ca", "caf", "café", "  ", "    ", "<|endoftext|>"]:
        vocab[token] = len(vocab)
    write_def(
        tmp_path,
        "nerdstash_tokenizer",
        {
            "config": {
                "splitRegex": r" ?\p{L}+| ?\d+| ?[^\t\n\f\r \p{L}\d]+|[\t\n\f\r ]+(?![^\t\n\f\r ])|[\t\n\f\r ]+"
            },
            "specialTokens": ["1", "  ", "    ", "<|endoftext|>"],
            "vocab": vocab,
            "merges": [("c", "a"), ("ca", "f"), ("caf", "é")],
        },
    )
    tokenizer = NaiTokenizer("nerdstash_tokenizer", tokenizer_model_path=tmp_path, download_session=NoDownload())
    assert tokenizer.encode("café 1\n") == [vocab["café"], vocab[" "], vocab["1"], vocab["0x0a"]]
    assert tokenizer.encode("    ") == [vocab["    "]]  # the longest special token, not two of "  "
    # digits are special tokens in nerdstash; decode() keeps them, drops only control markers
    assert tokenizer.decode(tokenizer.encode("café 1\n🙂<|endoftext|>")) == "café 1\n🙂"


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
