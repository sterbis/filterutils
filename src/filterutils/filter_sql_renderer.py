from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .filter import Filter
from .operators import Operator
from .unique_name_generator import UniqueNameGenerator

if TYPE_CHECKING:
    from .filter_node import FilterNode
    from .filter_tree import FilterTree


class FilterSqlRenderer:
    def render(
        self,
        filter_: Filter,
        *,
        column_map: dict[str, str] | None = None,
        name_generator: UniqueNameGenerator | None = None,
    ) -> tuple[str, dict[str, Any]]:
        from .filter_node import FilterNode
        from .filter_tree import FilterTree

        if isinstance(filter_, FilterTree):
            return self._render_tree(
                filter_,
                column_map=column_map,
                name_generator=name_generator,
            )

        if isinstance(filter_, FilterNode):
            return self._render_node(
                filter_,
                column_map=column_map,
                name_generator=name_generator,
            )

        raise TypeError(f"Unsupported filter type: {type(filter_).__name__}")

    def _render_node(
        self,
        filter_node: FilterNode,
        *,
        column_map: dict[str, str] | None = None,
        name_generator: UniqueNameGenerator | None = None,
    ) -> tuple[str, dict[str, Any]]:
        field = filter_node.field
        operator = filter_node.operator
        value = filter_node.value

        column = column_map.get(field, field) if column_map else field
        parameter_base_name = column.replace(".", "_")

        if value is None:
            return self._to_null_sql(column, operator)
        if operator == Operator.LIKE_ANY:
            return self._to_like_any_sql(
                column, parameter_base_name, value, name_generator
            )
        if operator in (Operator.IN, Operator.NOT_IN):
            return self._to_multi_value_sql(
                column, parameter_base_name, value, name_generator, operator
            )

        return self._to_single_value_sql(
            column, parameter_base_name, value, name_generator, operator
        )

    def _render_tree(
        self,
        filter_tree: FilterTree,
        *,
        column_map: dict[str, str] | None = None,
        name_generator: UniqueNameGenerator | None = None,
    ) -> tuple[str, dict[str, Any]]:
        logical_operator = filter_tree.logical_operator
        parentheses = filter_tree.parentheses
        name_generator = name_generator or UniqueNameGenerator(modify_first=True)

        sql_parts: list[str] = []
        parameters: dict[str, Any] = {}

        for child in filter_tree.children:
            child_sql, child_parameters = self.render(
                child,
                column_map=column_map,
                name_generator=name_generator,
            )
            sql_parts.append(child_sql)
            parameters.update(child_parameters)

        if not sql_parts:
            return "", {}

        sql = f" {logical_operator.to_sql()} ".join(sql_parts)
        if parentheses and len(sql_parts) > 1:
            sql = f"({sql})"

        return sql, parameters

    def _escape_value(self, value: str) -> str:
        return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    def _to_null_sql(
        self, column: str, operator: Operator
    ) -> tuple[str, dict[str, Any]]:
        sql = f"{column} {'IS NULL' if operator == Operator.EQ else 'IS NOT NULL'}"
        return sql, {}

    def _to_multi_value_sql(
        self,
        column: str,
        parameter_base_name: str,
        value: Any,
        name_generator: UniqueNameGenerator | None,
        operator: Operator,
    ) -> tuple[str, dict[str, Any]]:
        name_generator = name_generator or UniqueNameGenerator(modify_first=True)
        parameters: dict[str, Any] = {}
        placeholders = []

        for item in value:
            parameter_name = name_generator.next(parameter_base_name)
            placeholders.append(f":{parameter_name}")
            parameters[parameter_name] = item

        sql = f"{column} {operator.to_sql()} ({', '.join(placeholders)})"
        return sql, parameters

    def _to_single_value_sql(
        self,
        column: str,
        parameter_base_name: str,
        value: Any,
        name_generator: UniqueNameGenerator | None,
        operator: Operator,
    ) -> tuple[str, dict[str, Any]]:
        parameter_name = (
            name_generator.next(parameter_base_name)
            if name_generator
            else parameter_base_name
        )
        sql = f"{column} {operator.to_sql()} :{parameter_name}"
        sql_value = value
        if operator in (Operator.LIKE, Operator.NOT_LIKE):
            sql += " ESCAPE '\\'"
            sql_value = f"%{self._escape_value(value)}%"

        parameters = {parameter_name: sql_value}
        return sql, parameters

    def _to_like_any_sql(
        self,
        column: str,
        parameter_base_name: str,
        value: Any,
        name_generator: UniqueNameGenerator | None,
    ) -> tuple[str, dict[str, Any]]:
        name_generator = name_generator or UniqueNameGenerator(modify_first=True)
        parameters: dict[str, Any] = {}
        sql_parts = []
        for item in value:
            parameter_name = name_generator.next(parameter_base_name)
            sql_parts.append(
                f"{column} {Operator.LIKE.to_sql()} :{parameter_name} ESCAPE '\\'"
            )
            sql_value = f"%{self._escape_value(item)}%"
            parameters[parameter_name] = sql_value

        sql = f"({' OR '.join(sql_parts)})"
        return sql, parameters
