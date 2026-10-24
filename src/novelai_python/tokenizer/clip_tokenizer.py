"""CLIP BPE tokenizer (NovelAI Diffusion V1-V3 prompts) on top of ``kitoken``.

Gives the same token ids as OpenAI's ``SimpleTokenizer`` on ordinary prompts
(random prompts with unicode, case and whitespace variations) without the
``ftfy`` and ``regex`` dependencies. ``clean_text`` keeps the parts of
``ftfy.fix_text`` that matter for prompts: HTML entities, curly quotes,
ligatures and full/half-width forms.

Known differences from ``SimpleTokenizer``: ftfy's mojibake repair (cp1252
guessing) is dropped, and HTML-escaped curly quotes, the quotes ``„ ‟ ʼ``,
zero-width characters and a literal ``<|endoftext|>`` in the text give
different ids.
"""

import html
import re
import unicodedata
from functools import lru_cache
from typing import Any

from kitoken import Kitoken

from ._definition import added_token, bpe_model

__all__ = ["clean_text", "clip_definition", "decode"]

_SPLIT = r"""<\|startoftext\|>|<\|endoftext\|>|'s|'t|'re|'ve|'m|'ll|'d|[\p{L}]+|[\p{N}]|[^\s\p{L}\p{N}]+"""
_QUOTES = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"'})
# ligatures (U+FB00-FB06) and half/full-width forms (U+FF00-FFEF): NFKC folds them
# the same way ftfy does; NFKC is not applied to the rest of the text.
_COMPAT = re.compile(r"[ﬀ-ﬆ＀-￯Ǆ-ǌǱ-ǳ]+")


@lru_cache
def bytes_to_unicode() -> dict[int, str]:
    """GPT-2/CLIP reversible byte -> printable unicode table."""
    bs = list(range(ord("!"), ord("~") + 1)) + list(range(ord("¡"), ord("¬") + 1)) + list(range(ord("®"), ord("ÿ") + 1))
    cs = bs[:]
    n = 0
    for b in range(256):
        if b not in bs:
            bs.append(b)
            cs.append(256 + n)
            n += 1
    return dict(zip(bs, map(chr, cs), strict=True))


def clean_text(text: str) -> str:
    text = text.translate(_QUOTES)
    text = _COMPAT.sub(lambda m: unicodedata.normalize("NFKC", m.group()), text)
    return html.unescape(html.unescape(text))


def clip_definition(bpe_text: str) -> tuple[dict[str, Any], list[str]]:
    """The ``tokenizers``-format definition kitoken loads, built from NovelAI's ``clip_tokenizer.def``
    merges text, and the vocabulary in id order."""
    merges: list[tuple[str, str]] = []
    for line in bpe_text.split("\n")[1 : 49152 - 256 - 2 + 1]:
        left, right = line.split()
        merges.append((left, right))
    vocab = list(bytes_to_unicode().values())
    vocab = vocab + [v + "</w>" for v in vocab]
    vocab += ["".join(m) for m in merges]
    vocab += ["<|startoftext|>", "<|endoftext|>"]
    definition = {
        # kitoken needs the unknown token among the added ones; normalized=True keeps it from being
        # matched in the input text, as before.
        "added_tokens": [added_token(vocab.index("<|endoftext|>"), "<|endoftext|>", normalized=True)],
        "normalizer": {
            "type": "Sequence",
            "normalizers": [
                {"type": "NFC"},
                {"type": "Replace", "pattern": {"Regex": r"\s+"}, "content": " "},
                {"type": "StripNormalizer", "strip_left": True, "strip_right": True},
                {"type": "Lowercase"},
            ],
        },
        "pre_tokenizer": {
            "type": "Sequence",
            "pretokenizers": [
                {"type": "Split", "pattern": {"Regex": _SPLIT}, "behavior": "Removed", "invert": True},
                {"type": "ByteLevel", "add_prefix_space": False, "trim_offsets": True, "use_regex": False},
            ],
        },
        "model": bpe_model({t: i for i, t in enumerate(vocab)}, merges, unk="<|endoftext|>", suffix="</w>"),
    }
    return definition, vocab


def decode(tokenizer: Kitoken, ids: list[int]) -> str:
    return tokenizer.decode(ids).decode("utf-8", errors="replace").replace("</w>", " ")
