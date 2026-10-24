"""Parts of the ``tokenizers`` JSON format that ``kitoken.Kitoken.from_tokenizers`` reads.

NovelAI's ``.def`` files hold a vocabulary, merges and a split regex rather than a ready
``tokenizer.json``, so the definition is assembled here. Field names follow kitoken's
``convert/tokenizers.rs``; the strip normalizer, for one, is ``StripNormalizer`` there.
"""

from collections.abc import Iterable
from typing import Any

# JavaScript's \s. The site compiles splitRegex as a JavaScript RegExp; kitoken's fancy-regex takes \s as
# Unicode White_Space, which also has U+0085 and lacks U+FEFF, and \d as every Unicode digit, not 0-9.
_JS_SPACE = r"\t\n\x0B\f\r \u00A0\u1680\u2000-\u200A\u2028\u2029\u202F\u205F\u3000\uFEFF"


def js_regex(pattern: str) -> str:
    """``pattern`` with ``\\s``, ``\\S``, ``\\d`` and ``\\D`` spelled out the way JavaScript reads them."""
    out: list[str] = []
    in_class = False
    i = 0
    while i < len(pattern):
        char = pattern[i]
        if char == "\\" and i + 1 < len(pattern):
            escape = pattern[i + 1]
            if escape in "sd":
                body = _JS_SPACE if escape == "s" else "0-9"
                out.append(body if in_class else f"[{body}]")
            elif escape in "SD":
                if in_class:
                    raise ValueError(f"\\{escape} inside a character class is not supported: {pattern!r}")
                out.append(f"[^{_JS_SPACE if escape == 'S' else '0-9'}]")
            else:
                out.append(pattern[i : i + 2])
            i += 2
            continue
        if char == "[" and not in_class:
            in_class = True
        elif char == "]" and in_class:
            in_class = False
        out.append(char)
        i += 1
    return "".join(out)


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
    byte_fallback: bool = False,
) -> dict[str, Any]:
    """``byte_fallback`` makes kitoken encode what has no token through the ``<0xNN>`` byte tokens."""
    return {
        "type": "BPE",
        "dropout": None,
        "unk_token": unk,
        "continuing_subword_prefix": None,
        "end_of_word_suffix": suffix,
        "fuse_unk": False,
        "byte_fallback": byte_fallback,
        "ignore_merges": ignore_merges,
        "vocab": vocab,
        "merges": [list(m) for m in merges],
    }
