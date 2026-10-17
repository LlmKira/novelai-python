# src/novelai_python/tool/random_prompt/logic.py
import random
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class PromptOption:
    """One row of a tag table: ``[tag, weight, provides, requires, excludes]``."""

    tag: str | int
    weight: int
    provides: tuple[str, ...] = ()
    requires: tuple[str, ...] = ()
    excludes: tuple[str, ...] = ()

    @classmethod
    def from_row(cls, row: Sequence[Any]) -> "PromptOption":
        def tags(i: int) -> tuple[str, ...]:
            value = row[i] if len(row) > i else ()
            if isinstance(value, str):
                return (value,)
            # the web client's tables have a few malformed rows, e.g. ["opaque glasses", 12, 12, ...]
            return tuple(value) if isinstance(value, (list, tuple)) else ()

        return cls(row[0], int(row[1]), tags(2), tags(3), tags(4))


class TagConditions(Protocol):
    """A set of tags already in the prompt (a ``set`` or the V1 ``Conditions``)."""

    def __contains__(self, item: str, /) -> bool: ...
    def add(self, item: str, /) -> None: ...


def pick_option(rows: Sequence[Sequence[Any]], conditions: TagConditions | None = None) -> str | int:
    """
    Pick a weighted row. With ``conditions``, a row is skipped when one of its exclusions is
    already a condition or one of its requirements is missing, and the picked row adds the
    tags it provides. Without them every row can be picked. Returns "" when nothing fits.
    """
    options = [PromptOption.from_row(row) for row in rows]
    if conditions is not None:
        options = [
            o
            for o in options
            if not any(tag in conditions for tag in o.excludes) and all(tag in conditions for tag in o.requires)
        ]
    options = [o for o in options if o.weight > 0]
    if not options:
        return ""
    chosen = random.choices(options, weights=[o.weight for o in options])[0]
    if conditions is not None:
        for tag in chosen.provides:
            conditions.add(tag)
    return chosen.tag


class TagSelector:
    def __init__(self):
        self.selected_tags: set[str] = set()

    def weighted_choice(self, choices: Sequence[Sequence[Any]], simple: bool = False) -> str:
        return str(pick_option(choices, None if simple else self.selected_tags))

    def pick_count(self, ranges: Sequence[Sequence[Any]]) -> int:
        return int(pick_option(ranges) or 0)


def apply_curly_brackets(tag: str) -> str:
    if not tag:
        return ""
    if random.random() < 0.02:
        return f"{{{tag}}}"
    return tag


def js_random_int(min_val, max_val):
    """
    Эмуляция JS tf(max, min): floor(random * (max - min)) + min
    Верхняя граница НЕ включается в множитель, но результат сдвигается.
    Пример tf(3, 1) -> 1, 2.
    """
    return int(random.random() * (max_val - min_val)) + min_val
