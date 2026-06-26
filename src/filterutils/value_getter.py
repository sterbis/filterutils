from collections.abc import Mapping
from typing import Any


def default_value_getter(item: Any, field: str) -> Any:
    current = item
    for segment in field.split("."):
        if isinstance(current, Mapping):
            current = current[segment]
        else:
            current = getattr(current, segment)
    return current
