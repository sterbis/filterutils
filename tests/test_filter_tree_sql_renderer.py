import pytest

from filterutils import (
    FilterNode,
    FilterSqlRenderer,
    FilterTree,
    LogicalOperator,
    Operator,
)


def test_filter_sql_renderer_renders_filter_tree() -> None:
    tree = FilterTree(LogicalOperator.AND)
    tree.add_child(FilterNode("symbol", Operator.EQ, "AAPL"))
    tree.add_child(FilterNode("quantity", Operator.GT, 10))

    sql, parameters = FilterSqlRenderer().render(tree)

    assert sql == "symbol = :symbol_1 AND quantity > :quantity_1"
    assert parameters == {"symbol_1": "AAPL", "quantity_1": 10}


def test_filter_tree_exposes_children_collection() -> None:
    tree = FilterTree()
    child = FilterNode("symbol", Operator.EQ, "AAPL")

    tree.add_child(child)

    assert tree.children == [child]


def test_filter_tree_rejects_self_reference() -> None:
    tree = FilterTree()

    with pytest.raises(ValueError, match="Cannot add"):
        tree.add_child(tree)


def test_filter_tree_rejects_ancestor_reference() -> None:
    parent = FilterTree()
    child = FilterTree()
    grandchild = FilterTree()

    parent.add_child(child)
    child.add_child(grandchild)

    with pytest.raises(ValueError, match="Cannot add"):
        grandchild.add_child(parent)
