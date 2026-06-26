from typing import Any

from .filter import Filter, TItem, ValueGetter
from .filter_sql_renderer import FilterSqlRenderer
from .operators import LogicalOperator
from .unique_name_generator import UniqueNameGenerator


class FilterTree(Filter):
    def __init__(
        self,
        logical_operator: LogicalOperator = LogicalOperator.AND,
        parentheses: bool = False,
    ) -> None:
        self._logical_operator = logical_operator
        self._parentheses = parentheses
        self._children: list[Filter] = []
        self._parent: FilterTree | None = None

    @property
    def parentheses(self) -> bool:
        return self._parentheses

    @property
    def logical_operator(self) -> LogicalOperator:
        return self._logical_operator

    @property
    def children(self) -> list[Filter]:
        return list(self._children)

    @property
    def parent(self) -> FilterTree | None:
        return self._parent

    def set_parent(self, parent: FilterTree | None) -> None:
        self._parent = parent

    def add_child(self, filter_: Filter) -> None:
        if filter_ is self:
            raise ValueError("Cannot add a FilterTree to itself")

        if isinstance(filter_, FilterTree):
            current = self.parent
            while current is not None:
                if current is filter_:
                    raise ValueError("Cannot add an ancestor FilterTree as a child")
                current = current.parent

            filter_.set_parent(self)

        self._children.append(filter_)

    def match(
        self,
        item: TItem,
        value_getter: ValueGetter[TItem] | None = None,
    ) -> bool:
        if not self.children:
            return True

        if self._logical_operator == LogicalOperator.AND:
            return all(filter_.match(item, value_getter) for filter_ in self.children)

        return any(filter_.match(item, value_getter) for filter_ in self.children)

    def to_sql(
        self,
        column_map: dict[str, str] | None = None,
        name_generator: UniqueNameGenerator | None = None,
    ) -> tuple[str, dict[str, Any]]:
        return FilterSqlRenderer().render(
            self,
            column_map=column_map,
            name_generator=name_generator,
        )
