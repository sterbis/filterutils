from dataclasses import dataclass
from typing import Any

from .exceptions import FilterEvaluationError
from .filter import Filter, TItem, ValueGetter
from .filter_node_validation import validate_filter_node
from .filter_sql_renderer import FilterSqlRenderer
from .operators import Operator
from .unique_name_generator import UniqueNameGenerator
from .value_getter import default_value_getter


@dataclass(frozen=True)
class FilterNode(Filter):
    field: str
    operator: Operator
    value: Any

    def __post_init__(self) -> None:
        validate_filter_node(self.operator, self.value)

    def match(
        self,
        item: TItem,
        value_getter: ValueGetter[TItem] | None = None,
    ) -> bool:
        getter = value_getter or default_value_getter
        try:
            value = getter(item, self.field)
        except (AttributeError, KeyError):
            return False

        return self._compare(value)

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

    def _is_like(self, value: Any, pattern: str) -> bool:
        if value is None:
            return False

        if isinstance(value, bool):
            return False

        return pattern.lower() in str(value).lower()

    def _is_like_any(self, value: Any, patterns: list[str]) -> bool:
        for pattern in patterns:
            if pattern.lower() in str(value).lower():
                return True

        return False

    def _compare(self, value: Any) -> bool:
        try:
            return self.operator.compare(
                value,
                self.value,
                like_handler=self._is_like,
                like_any_handler=self._is_like_any,
            )
        except TypeError as error:
            raise FilterEvaluationError(
                f"Failed to compare '{self.field}' field value: {value} {self.operator} {self.value}"
            ) from error
