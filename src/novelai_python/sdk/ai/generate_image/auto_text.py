# @File    : auto_text.py
"""
The web client's auto text block for V5.

When the prompt has text in quotes and no ``Text:`` of its own, novelai.net appends
``, teXt: <quoted texts>`` to the end of the base prompt. Text rendering reads the text
from that block, which has to come last (docs.novelai.net/en/image/textrendering).
Separate texts are joined by an empty line. Ported from the web client.
"""

import re
from collections.abc import Sequence
from typing import Any

__all__ = ["apply_auto_text", "strip_auto_text"]

_USER_TEXT_RE = re.compile(r"(?:^|\s|[,.:\[\]{}、。])text:(?!:)", re.I)
_AUTO_TEXT_RE = re.compile(r"(?:^|\s|[,.:\[\]{}、。])teXt:(?!:)")
_QUOTE_PAIRS = {'"': '"', "“": "”", "「": "」", "'": "'", "‘": "’"}
_CJK_RE = re.compile(r"[　-〿぀-ゟ゠-ヿ＀-ﾟ一-龯㐀-䶿]")
_SEG_MAX = 6
_ESCAPED_PIPE = "\U000103b9"


def _split_segments(prompt: str) -> list[str]:
    """Split on '|' like the web client; '||' is an escaped pipe and does not split."""
    segs = prompt.replace("||", _ESCAPED_PIPE).split("|")
    out = segs[: _SEG_MAX - 1]
    if len(segs) > _SEG_MAX - 1:
        out.append("|".join(segs[_SEG_MAX - 1 :]))
    return [s.replace(_ESCAPED_PIPE, "||") for s in out]


def _quoted_texts(s: str) -> list[str]:
    out, i = [], 0
    while i < len(s):
        close = _QUOTE_PAIRS.get(s[i])
        # an apostrophe opens a quote only at the start of a word
        if close is None or (s[i] == "'" and i > 0 and not re.match(r"[\s,.]", s[i - 1])):
            i += 1
            continue
        apostrophe = close in ("'", "’")
        j = i + 1
        while j < len(s) and (s[j] != close or (apostrophe and j + 1 < len(s) and re.match(r"[^\W_]", s[j + 1]))):
            j += 1
        if j >= len(s):
            i += 1
            continue
        text = s[i + 1 : j].strip()
        if text:
            out.append(text)
        i = j + 1
    return out


def _order_by_position(chars: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Characters top to bottom, left to right within a row, as the web client orders them."""

    def rows(cs: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
        if len(cs) <= 1:
            return [cs]
        span = cs[-1]["center"]["y"] - cs[0]["center"]["y"]
        cut, gap = 1, -1.0
        for k in range(1, len(cs)):
            d = cs[k]["center"]["y"] - cs[k - 1]["center"]["y"]
            if d > gap:
                gap, cut = d, k
        if span <= 0.15 and gap <= 0.1:
            return [cs]
        return rows(cs[:cut]) + rows(cs[cut:])

    ordered = sorted(chars, key=lambda c: c["center"]["y"])
    return [c for row in rows(ordered) for c in sorted(row, key=lambda c: c["center"]["x"])]


def _collect_texts(base: str, chars: Sequence[dict[str, Any]], use_coords: bool) -> list[str]:
    enabled = [c for c in chars if c.get("enabled", True) and c.get("prompt")]
    if use_coords:
        enabled = _order_by_position(enabled)
    groups = [_quoted_texts(base)] + [_quoted_texts(c["prompt"]) for c in enabled]
    flat = "".join(t for g in groups for t in g)
    if flat and len(_CJK_RE.findall(flat)) / len(flat) > 0.3:
        groups = [list(reversed(g)) for g in groups]
    return [t for g in groups for t in g]


def apply_auto_text(prompt: str, chars: Sequence[dict[str, Any]] = (), use_coords: bool = False) -> str:
    """
    Append ``, teXt: …`` with every quoted text of the base prompt and the characters.
    Nothing changes when the user wrote ``Text:`` anywhere or quoted nothing.

    :param chars: character prompts as dicts (``prompt``, ``enabled``, ``center: {x, y}``).
    """
    if _USER_TEXT_RE.search(prompt) or any(
        _USER_TEXT_RE.search(c.get("prompt") or "") for c in chars if c.get("enabled", True)
    ):
        return prompt
    segs = _split_segments(prompt)
    texts = _collect_texts(segs[0], chars, use_coords)
    if not texts:
        return prompt
    block = "teXt: " + "\n\n".join(texts)
    head = re.sub(r"[\s,]+$", "", segs[0])
    segs[0] = f"{head}, {block}" if head else block
    return "|".join(segs)


def strip_auto_text(prompt: str, chars: Sequence[dict[str, Any]] = (), use_coords: bool = False) -> str:
    """Remove a ``teXt:`` block that apply_auto_text would have added; text the user wrote stays."""
    out = []
    for seg in _split_segments(prompt):
        m = _AUTO_TEXT_RE.search(seg)
        if not m:
            out.append(seg)
            continue
        before = seg[: m.start()]
        if seg[m.end() :].strip() != "\n\n".join(_collect_texts(before, chars, use_coords)):
            out.append(seg)
        else:
            out.append(re.sub(r"[\s,]+$", "", before))
    return "|".join(out)
