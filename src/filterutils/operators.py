from enum import StrEnum
from typing import Any, Callable


class Operator(StrEnum):
    LT = "<"
    LE = "<="
    EQ = "="
    NE = "!="
    GE = ">="
    GT = ">"
    LIKE = "~"
    NOT_LIKE = "!~"
    IN = "IN"
    NOT_IN = "NOT IN"
    LIKE_ANY = "LIKE ANY"

    def to_sql(self) -> str:
        sql: dict[Operator, str] = {
            Operator.LIKE: "LIKE",
            Operator.NOT_LIKE: "NOT LIKE",
        }
        if self == Operator.LIKE_ANY:
            raise RuntimeError(f"Operator {self} cannot be converted to SQL.")

        return sql.get(self, self.value)

    def compare(
        self,
        left: Any,
        right: Any,
        *,
        like_handler: Callable[[Any, str], bool] | None = None,
        like_any_handler: Callable[[Any, list[str]], bool] | None = None,
    ) -> bool:
        if self == Operator.LT:
            return bool(left < right)
        if self == Operator.LE:
            return bool(left <= right)
        if self == Operator.EQ:
            return bool(left == right)
        if self == Operator.NE:
            return bool(left != right)
        if self == Operator.GE:
            return bool(left >= right)
        if self == Operator.GT:
            return bool(left > right)
        if self == Operator.LIKE:
            return self._compare_like(left, right, like_handler)
        if self == Operator.NOT_LIKE:
            return not self._compare_like(left, right, like_handler)
        if self == Operator.IN:
            return left in right
        if self == Operator.NOT_IN:
            return left not in right
        if self == Operator.LIKE_ANY:
            if like_any_handler is None:
                raise TypeError("LIKE ANY requires a like-any handler")
            return like_any_handler(left, right)

        raise ValueError(f"Unsupported operator: {self}")

    def _compare_like(
        self,
        left: Any,
        right: Any,
        like_handler: Callable[[Any, str], bool] | None = None,
    ) -> bool:
        if like_handler is None:
            raise TypeError("LIKE requires a like handler")
        return like_handler(left, right)


class LogicalOperator(StrEnum):
    AND = "AND"
    OR = "OR"

    def to_sql(self) -> str:
        return self.value
