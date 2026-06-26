"""Filtering utilities.

Provides classes to parse textual filter expressions, evaluate them
against Python objects, and convert them to parameterized SQL
fragments. Default in-memory evaluation uses attribute access on
objects; mapping (dict-like) access is also supported. Custom
`value_getter(item, field)` can be provided to override lookup.
"""

from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator
from typing import Any, Callable, TypeVar

from .unique_name_generator import UniqueNameGenerator

TItem = TypeVar("TItem")
ValueGetter = Callable[[TItem, str], Any]


class Filter(ABC):
    def apply(
        self,
        items: Iterable[TItem],
        value_getter: ValueGetter[TItem] | None = None,
    ) -> Iterator[TItem]:
        for item in items:
            if self.match(item, value_getter):
                yield item

    @abstractmethod
    def match(
        self,
        item: TItem,
        value_getter: ValueGetter[TItem] | None = None,
    ) -> bool: ...

    @abstractmethod
    def to_sql(
        self,
        column_map: dict[str, str] | None = None,
        name_generator: UniqueNameGenerator | None = None,
    ) -> tuple[str, dict[str, Any]]: ...


class NullFilter(Filter):
    def match(
        self,
        item: TItem,
        value_getter: ValueGetter[TItem] | None = None,
    ) -> bool:
        return True

    def to_sql(
        self,
        column_map: dict[str, str] | None = None,
        name_generator: UniqueNameGenerator | None = None,
    ) -> tuple[str, dict[str, Any]]:
        return "", {}
