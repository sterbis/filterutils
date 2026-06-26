from typing import Any

from .exceptions import FilterConfigurationError
from .operators import Operator


def validate_filter_node(operator: Operator, value: Any) -> None:
    if operator in (Operator.IN, Operator.NOT_IN, Operator.LIKE_ANY):
        if not isinstance(value, (list, tuple, set)):
            raise FilterConfigurationError(
                f"'{operator}' operator requires a collection, got '{type(value).__name__}'."
            )

        if None in value:
            raise FilterConfigurationError(
                f"'None' value is not supported in the collection: {value}."
            )

        if operator == Operator.LIKE_ANY and not all(
            isinstance(item, str) for item in value
        ):
            raise FilterConfigurationError(
                f"'{operator}' operator requires a collection of strings, got {value}."
            )

    if operator in (Operator.LIKE, Operator.NOT_LIKE):
        if not isinstance(value, str):
            raise FilterConfigurationError(
                f"'{operator}' operator requires a string value, got '{type(value).__name__}'"
            )

    if value is None and operator not in (Operator.EQ, Operator.NE):
        raise FilterConfigurationError(
            f"Only '{Operator.EQ}' or '{Operator.NE}' operator is supported for 'None' value, got '{operator}'."
        )
