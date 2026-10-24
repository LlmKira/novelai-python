"""Parts of the ``tokenizers`` JSON format that ``kitoken.Kitoken.from_tokenizers`` reads.

NovelAI's ``.def`` files hold a vocabulary, merges and a split regex rather than a ready
``tokenizer.json``, so the definition is assembled here. Field names follow kitoken's
``convert/tokenizers.rs``; the strip normalizer, for one, is ``StripNormalizer`` there.
"""

from collections.abc import Iterable
from typing import Any


def added_token(token_id: int, content: str, normalized: bool = False) -> dict[str, Any]:
    """A special token; ``normalized=False`` makes it match in the raw input text."""
    return {
        "id": token_id,
        "content": content,
        "single_word": False,
        "lstrip": False,
        "rstrip": False,
        "normalized": normalized,
        "special": True,
    }


def bpe_model(
    vocab: dict[str, int],
    merges: Iterable[tuple[str, str]],
    unk: str | None = None,
    suffix: str | None = None,
    ignore_merges: bool = False,
) -> dict[str, Any]:
    return {
        "type": "BPE",
        "dropout": None,
        "unk_token": unk,
        "continuing_subword_prefix": None,
        "end_of_word_suffix": suffix,
        "fuse_unk": False,
        "byte_fallback": False,
        "ignore_merges": ignore_merges,
        "vocab": vocab,
        "merges": [list(m) for m in merges],
    }
