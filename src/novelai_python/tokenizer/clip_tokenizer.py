"""CLIP BPE tokenizer (NovelAI Diffusion V1-V3 prompts) on top of HF ``tokenizers``.

Reproduces OpenAI's ``SimpleTokenizer`` token ids (checked on 3000 random
prompts with unicode, case and whitespace variations) without the ``ftfy`` and
``regex`` dependencies. ``clean_text`` keeps the parts of ``ftfy.fix_text`` that
matter for prompts: HTML entities, curly quotes, ligatures and full/half-width
forms. Mojibake repair (``ftfy``'s cp1252 guessing) is intentionally dropped.
"""

import html
import re
import unicodedata
from functools import lru_cache

from tokenizers import Regex, Tokenizer, normalizers, pre_tokenizers
from tokenizers.models import BPE

__all__ = ["build_clip_tokenizer", "clean_text", "decode"]

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


def build_clip_tokenizer(bpe_text: str) -> Tokenizer:
    """Build the tokenizer from NovelAI's ``clip_tokenizer.def`` merges text."""
    merges: list[tuple[str, str]] = []
    for line in bpe_text.split("\n")[1 : 49152 - 256 - 2 + 1]:
        left, right = line.split()
        merges.append((left, right))
    vocab = list(bytes_to_unicode().values())
    vocab = vocab + [v + "</w>" for v in vocab]
    vocab += ["".join(m) for m in merges]
    vocab += ["<|startoftext|>", "<|endoftext|>"]
    tok = Tokenizer(
        BPE(
            vocab={t: i for i, t in enumerate(vocab)},
            merges=merges,
            end_of_word_suffix="</w>",
            unk_token="<|endoftext|>",
        )
    )
    tok.normalizer = normalizers.Sequence(
        [normalizers.NFC(), normalizers.Replace(Regex(r"\s+"), " "), normalizers.Strip(), normalizers.Lowercase()]
    )
    tok.pre_tokenizer = pre_tokenizers.Sequence(
        [
            pre_tokenizers.Split(Regex(_SPLIT), behavior="removed", invert=True),
            pre_tokenizers.ByteLevel(add_prefix_space=False, use_regex=False),
        ]
    )
    return tok


def decode(tokenizer: Tokenizer, ids: list[int]) -> str:
    byte_decoder = {v: k for k, v in bytes_to_unicode().items()}
    text = "".join(tokenizer.id_to_token(i) or "" for i in ids)
    return bytes(byte_decoder[c] for c in text).decode("utf-8", errors="replace").replace("</w>", " ")
