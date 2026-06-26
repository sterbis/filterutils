from filterutils import (
    FilterNode,
    FilterTree,
    LogicalOperator,
    Operator,
)


class NestedItem:
    def __init__(self, value: int) -> None:
        self.value = value


class DummyItem:
    def __init__(self, symbol: str, nested: object | None = None) -> None:
        self.symbol = symbol
        self.nested = nested or NestedItem(0)


def test_filter_match_with_attribute_access() -> None:
    item = DummyItem(symbol="AAPL")
    filter_ = FilterNode("symbol", Operator.GE, "AAPL")

    assert filter_.match(item)
    assert list(filter_.apply([item])) == [item]


def test_filter_match_with_mapping_access() -> None:
    item = {"symbol": "AAPL", "nested": {"value": 10}}
    filter_ = FilterNode("symbol", Operator.EQ, "AAPL")

    assert filter_.match(item)
    assert list(filter_.apply([item])) == [item]


def test_filter_match_with_nested_attribute_access() -> None:
    item = DummyItem(symbol="AAPL", nested=NestedItem(10))
    filter_ = FilterNode("nested.value", Operator.EQ, 10)

    assert filter_.match(item)
    assert list(filter_.apply([item])) == [item]


def test_filter_match_with_nested_mapping_access() -> None:
    item = {"symbol": "AAPL", "nested": {"value": 10}}
    filter_ = FilterNode("nested.value", Operator.EQ, 10)

    assert filter_.match(item)
    assert list(filter_.apply([item])) == [item]


def test_filter_tree_combines_attribute_and_mapping_filters() -> None:
    attribute_item = DummyItem(symbol="AAPL", nested=NestedItem(10))
    mapping_item = {"symbol": "AAPL", "nested": {"value": 10}}

    tree = FilterTree()
    tree.add_child(FilterNode("symbol", Operator.EQ, "AAPL"))
    tree.add_child(FilterNode("nested.value", Operator.EQ, 10))

    assert tree.match(attribute_item)
    assert tree.match(mapping_item)
    assert list(tree.apply([attribute_item, mapping_item])) == [
        attribute_item,
        mapping_item,
    ]


def test_filter_tree_and_logic_rejects_partial_matches() -> None:
    attribute_item = DummyItem(symbol="AAPL", nested=NestedItem(10))
    mapping_item = {"symbol": "AAPL", "nested": {"value": 10}}

    tree = FilterTree()
    tree.add_child(FilterNode("symbol", Operator.EQ, "AAPL"))
    tree.add_child(FilterNode("nested.value", Operator.EQ, 20))

    assert not tree.match(attribute_item)
    assert not tree.match(mapping_item)
    assert list(tree.apply([attribute_item, mapping_item])) == []


def test_filter_tree_nested_and_or_logic() -> None:
    attribute_item = DummyItem(symbol="AAPL", nested=NestedItem(10))
    mapping_item = {"symbol": "AAPL", "nested": {"value": 20}}
    attribute_item_2 = DummyItem(symbol="GOOGL", nested=NestedItem(10))
    mapping_item_2 = {"symbol": "MSFT", "nested": {"value": 20}}

    or_tree = FilterTree(LogicalOperator.OR, parentheses=True)
    or_tree.add_child(FilterNode("symbol", Operator.EQ, "AAPL"))
    or_tree.add_child(FilterNode("symbol", Operator.EQ, "GOOGL"))

    tree = FilterTree()
    tree.add_child(FilterNode("nested.value", Operator.GE, 20))
    tree.add_child(or_tree)

    assert not tree.match(attribute_item)
    assert tree.match(mapping_item)
    assert not tree.match(attribute_item_2)
    assert not tree.match(mapping_item_2)
    assert list(
        tree.apply([attribute_item, mapping_item, attribute_item_2, mapping_item_2])
    ) == [mapping_item]
