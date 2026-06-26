import re
from typing import Any, Callable

from .exceptions import (
    FilterConfigurationError,
    FilterExpressionError,
    FilterExpressionParsingError,
)
from .filter import Filter
from .filter_node import FilterNode
from .filter_tree import FilterTree
from .operators import Operator

ValueParser = Callable[[str], Any]


class FilterExpressionParser:

    @classmethod
    def parse(
        cls,
        field: str,
        expression: str,
        value_parser: ValueParser | None = None,
    ) -> Filter:
        expression = expression.strip()
        if not expression:
            raise FilterExpressionError(
                expression, "Cannot create filter from empty expression."
            )

        if "..." in expression or ".." in expression:
            parsing_method = cls._parse_range_expression
        else:
            parsing_method = cls._parse_expression

        try:
            return parsing_method(field, expression, value_parser)
        except FilterExpressionParsingError as error:
            raise FilterExpressionError(expression, str(error)) from error

    @classmethod
    def _parse_expression(
        cls,
        field: str,
        expression: str,
        value_parser: ValueParser | None = None,
    ) -> Filter:
        operator_expression, value_expression = cls._split_expression(expression)
        values = cls._parse_value_expression(value_expression, value_parser)

        if not values:
            raise FilterExpressionParsingError("No value provided.")

        if len(values) > 1:
            operator = cls._parse_multi_value_operator_expression(operator_expression)
            value: Any = values

        else:
            operator = cls._parse_single_value_operator_expression(operator_expression)
            value = values[0]

        try:
            return FilterNode(field, operator, value)
        except FilterConfigurationError as error:
            raise FilterExpressionParsingError(str(error)) from error

    @classmethod
    def _parse_range_expression(
        cls,
        field: str,
        expression: str,
        value_parser: ValueParser | None = None,
    ) -> Filter:
        separators = re.findall(r"\.{2,}", expression)
        if not separators:
            raise FilterExpressionParsingError("Missing range separator '..' or '...'.")

        if len(separators) > 1:
            raise FilterExpressionParsingError(
                "Range separator '..' or '...' can only occur once in expression.",
            )

        separator = separators[0]
        if len(separator) > 3:
            raise FilterExpressionParsingError(
                f"Invalid range separator: '{separator}'.",
            )

        parts = [part.strip() for part in expression.split(separator)]
        if not any(parts):
            raise FilterExpressionParsingError("No value provided.")

        filters: list[FilterNode] = []
        for index, part in enumerate(parts):
            if not part:
                continue

            filter_ = cls._parse_expression_part(
                part, index, field, separator, value_parser
            )

            filters.append(filter_)

        if len(filters) > 1:
            lower_bound = filters[0].value
            upper_bound = filters[1].value
            if lower_bound >= upper_bound:
                raise FilterExpressionParsingError(
                    f"Range lower bound '{lower_bound}' greater than or equal to upper bound '{upper_bound}'.",
                )

            filter_tree = FilterTree()
            for filter_ in filters:
                filter_tree.add_child(filter_)

            return filter_tree

        return filters[0]

    @classmethod
    def _parse_expression_part(
        cls,
        part: str,
        index: int,
        field: str,
        separator: str,
        value_parser: ValueParser | None = None,
    ) -> FilterNode:
        operator_expression, value_expression = cls._split_expression(part)

        if operator_expression:
            raise FilterExpressionParsingError(
                f"No operator allowed when using range seprator '..' or '...'. Found operator: '{operator_expression}'.",
            )

        values = cls._parse_value_expression(value_expression, value_parser)

        if len(values) != 1:
            raise FilterExpressionParsingError(
                f"Invalid value provided as range boundary: '{value_expression}'.",
            )

        value = values[0]
        if value is None:
            raise FilterExpressionParsingError(
                f"Invalid value provided as range boundary: '{value_expression}'.",
            )

        match (index, separator):
            case (0, ".."):
                operator = Operator.GE

            case (0, "..."):
                operator = Operator.GT

            case (1, ".."):
                operator = Operator.LE

            case (1, "..."):
                operator = Operator.LT

        return FilterNode(field, operator, value)

    @classmethod
    def _split_expression(cls, expression: str) -> tuple[str, str]:
        match = re.match(r"(=|!=|>=|>|<=|<|~|!~)?\s*(.*)", expression)
        if match is None:
            raise FilterExpressionParsingError(
                f"No operator or value found in expression or expression part: '{expression}'."
            )

        operator_expression, value_expression = match.groups()
        return operator_expression, value_expression

    @classmethod
    def _parse_single_value_operator_expression(
        cls,
        operator_expression: str,
    ) -> Operator:
        if operator_expression:
            try:
                return Operator(operator_expression)
            except ValueError as error:
                raise FilterExpressionParsingError(
                    f"Invalid operator expression: '{operator_expression}'"
                ) from error

        return Operator.EQ

    @classmethod
    def _parse_multi_value_operator_expression(
        cls, operator_expression: str
    ) -> Operator:
        if not operator_expression or operator_expression == "=":
            return Operator.IN
        if operator_expression == "!=":
            return Operator.NOT_IN
        if operator_expression == "~":
            return Operator.LIKE_ANY

        raise FilterExpressionParsingError(
            f"Invalid operator for multi value expression: '{operator_expression}'."
        )

    @classmethod
    def _parse_value_expression(
        cls, value_expression: str, value_parser: ValueParser | None = None
    ) -> list[Any]:
        values: list[Any] = []
        for value in value_expression.split(","):
            value = value.strip()
            if not value:
                continue

            if value.lower() == "null":
                values.append(None)
            elif value_parser is not None:
                try:
                    values.append(value_parser(value))
                except Exception as error:
                    raise FilterExpressionParsingError(
                        f"Failed to parse value '{value}' with provided parser '{value_parser}'."
                    ) from error

            else:
                values.append(value)

        return values
