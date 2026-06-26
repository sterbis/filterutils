import pytest

from filterutils.exceptions import FilterConfigurationError
from filterutils.filter_node_validation import validate_filter_node
from filterutils.operators import Operator


def test_validate_filter_node_accepts_valid_collection_value() -> None:
    validate_filter_node(Operator.IN, ["AAPL", "GOOGL"])


def test_validate_filter_node_rejects_non_collection_value() -> None:
    with pytest.raises(FilterConfigurationError):
        validate_filter_node(Operator.IN, "AAPL")


def test_validate_filter_node_rejects_none_in_collection() -> None:
    with pytest.raises(FilterConfigurationError):
        validate_filter_node(Operator.IN, ["AAPL", None])


def test_validate_filter_node_rejects_like_any_with_non_string_values() -> None:
    with pytest.raises(FilterConfigurationError):
        validate_filter_node(Operator.LIKE_ANY, ["AAPL", 2])


def test_validate_filter_node_rejects_non_string_value_for_like() -> None:
    with pytest.raises(FilterConfigurationError):
        validate_filter_node(Operator.LIKE, 10)


def test_validate_filter_node_rejects_non_string_value_for_not_like() -> None:
    with pytest.raises(FilterConfigurationError):
        validate_filter_node(Operator.NOT_LIKE, 10)


def test_validate_filter_node_accepts_string_value_for_like() -> None:
    validate_filter_node(Operator.LIKE, "trading")


def test_validate_filter_node_rejects_none_for_non_equality_operator() -> None:
    with pytest.raises(FilterConfigurationError):
        validate_filter_node(Operator.GT, None)


def test_validate_filter_node_accepts_none_for_equality_operators() -> None:
    validate_filter_node(Operator.EQ, None)
    validate_filter_node(Operator.NE, None)
