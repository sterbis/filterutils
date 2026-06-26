import re
from decimal import Decimal
from datetime import date, datetime
from typing import Any, Callable

import pytest

from filterutils import (
    FilterExpressionError,
    FilterExpressionParser,
)

filter_expression_to_sql_data = [
    ("symbol", "AAPL", None, "symbol = :symbol", {"symbol": "AAPL"}),
    ("symbol", "  AAPL   ", None, "symbol = :symbol", {"symbol": "AAPL"}),
    ("symbol", "=GOOGL", None, "symbol = :symbol", {"symbol": "GOOGL"}),
    ("symbol", "  =GOOGL", None, "symbol = :symbol", {"symbol": "GOOGL"}),
    ("symbol", "!=MSFT", None, "symbol != :symbol", {"symbol": "MSFT"}),
    ("symbol", "  != MSFT", None, "symbol != :symbol", {"symbol": "MSFT"}),
    (
        "platform",
        "~trading",
        None,
        "platform LIKE :platform ESCAPE '\\'",
        {"platform": "%trading%"},
    ),
    (
        "platform",
        "!~ibkr",
        None,
        "platform NOT LIKE :platform ESCAPE '\\'",
        {"platform": "%ibkr%"},
    ),
    (
        "name",
        "~my_100%_profit_account",
        None,
        "name LIKE :name ESCAPE '\\'",
        {"name": "%my\\_100\\%\\_profit\\_account%"},
    ),
    ("name", "null", None, "name IS NULL", {}),
    ("name", "=null", None, "name IS NULL", {}),
    ("name", "!=null", None, "name IS NOT NULL", {}),
    ("quantity", "0", Decimal, "quantity = :quantity", {"quantity": Decimal("0")}),
    (
        "unrealized_pnl_percent",
        ">=10",
        lambda value: Decimal(value) / 100,
        "unrealized_pnl_percent >= :unrealized_pnl_percent",
        {"unrealized_pnl_percent": Decimal("0.1")},
    ),
    (
        "opened_date",
        "> 2026-01-01",
        date.fromisoformat,
        "opened_date > :opened_date",
        {"opened_date": date(2026, 1, 1)},
    ),
    (
        "last_buy_at",
        "< 2023-01-01 12:30:45",
        datetime.fromisoformat,
        "last_buy_at < :last_buy_at",
        {"last_buy_at": datetime(2023, 1, 1, 12, 30, 45)},
    ),
    (
        "symbol",
        "AAPL, GOOGL, MSFT",
        None,
        "symbol IN (:symbol_1, :symbol_2, :symbol_3)",
        {"symbol_1": "AAPL", "symbol_2": "GOOGL", "symbol_3": "MSFT"},
    ),
    (
        "symbol",
        "= AAPL, GOOGL, MSFT",
        None,
        "symbol IN (:symbol_1, :symbol_2, :symbol_3)",
        {"symbol_1": "AAPL", "symbol_2": "GOOGL", "symbol_3": "MSFT"},
    ),
    (
        "symbol",
        "!= AAPL, GOOGL, MSFT",
        None,
        "symbol NOT IN (:symbol_1, :symbol_2, :symbol_3)",
        {"symbol_1": "AAPL", "symbol_2": "GOOGL", "symbol_3": "MSFT"},
    ),
    (
        "symbol",
        "~ BRK._, GE._",
        None,
        "(symbol LIKE :symbol_1 ESCAPE '\\' OR symbol LIKE :symbol_2 ESCAPE '\\')",
        {"symbol_1": "%BRK.\\_%", "symbol_2": "%GE.\\_%"},
    ),
    ("symbol", "AAPL, ", None, "symbol = :symbol", {"symbol": "AAPL"}),
    (
        "symbol",
        "AAPL, GOOGL, ",
        None,
        "symbol IN (:symbol_1, :symbol_2)",
        {"symbol_1": "AAPL", "symbol_2": "GOOGL"},
    ),
    (
        "price",
        "100..200",
        int,
        "price >= :price_1 AND price <= :price_2",
        {"price_1": 100, "price_2": 200},
    ),
    (
        "price",
        "100...200",
        int,
        "price > :price_1 AND price < :price_2",
        {"price_1": 100, "price_2": 200},
    ),
    (
        "price",
        "100..",
        int,
        "price >= :price",
        {"price": 100},
    ),
    (
        "price",
        "...200",
        int,
        "price < :price",
        {"price": 200},
    ),
]

invalid_filter_expression_data = [
    ("symbol", "", None, "Cannot create filter from empty expression."),
    ("symbol", "  ", None, "Cannot create filter from empty expression."),
    (
        "symbol",
        "AAPL",
        int,
        "Failed to parse value 'AAPL' with provided parser '<class 'int'>'.",
    ),
    ("symbol", "~ ", None, "No value provided."),
    ("symbol", ", ", None, "No value provided."),
    (
        "symbol",
        "!~ AAPL, GOOGL",
        None,
        "Invalid operator for multi value expression: '!~'.",
    ),
    (
        "price",
        "> null",
        None,
        "Only '=' or '!=' operator is supported for 'None' value, got '>'.",
    ),
    (
        "symbol",
        "AAPL, null",
        None,
        "'None' value is not supported in the collection: ['AAPL', None].",
    ),
    ("price", "~100", int, "'~' operator requires a string value, got 'int'"),
    (
        "price",
        "~100, 200",
        int,
        "'LIKE ANY' operator requires a collection of strings, got [100, 200].",
    ),
    ("symbol", "..", None, "No value provided."),
    ("symbol", "...", None, "No value provided."),
    ("symbol", "....", None, "Invalid range separator: '....'."),
    (
        "price",
        "100..200..300",
        None,
        "Range separator '..' or '...' can only occur once in expression.",
    ),
    (
        "price",
        ">100..<200",
        None,
        "No operator allowed when using range seprator '..' or '...'. Found operator: '>'.",
    ),
    (
        "price",
        "100, 200...",
        None,
        "Invalid value provided as range boundary: '100, 200'.",
    ),
    ("price", "null...200", None, "Invalid value provided as range boundary: 'null'."),
    (
        "price",
        "200...100",
        None,
        "Range lower bound '200' greater than or equal to upper bound '100'.",
    ),
]


@pytest.mark.parametrize(
    "field, expression, value_parser, expected_sql, expected_parameters",
    filter_expression_to_sql_data,
)
def test_filter_expression_to_sql(
    field: str,
    expression: str,
    value_parser: Callable[[str], Any] | None,
    expected_sql: str,
    expected_parameters: dict[str, Any],
) -> None:
    filter_ = FilterExpressionParser.parse(field, expression, value_parser)
    sql, parameters = filter_.to_sql()
    assert sql == expected_sql
    assert parameters == expected_parameters


@pytest.mark.parametrize(
    "field, expression, value_parser, detail", invalid_filter_expression_data
)
def test_invalid_filter_expression(
    field: str,
    expression: str,
    value_parser: Callable[[str], Any] | None,
    detail: str,
) -> None:
    expected_error_message = re.escape(
        f"Invalid filter expression: '{expression.strip()}'. {detail}"
    )
    with pytest.raises(FilterExpressionError, match=expected_error_message):
        print(repr(FilterExpressionParser.parse(field, expression, value_parser)))
