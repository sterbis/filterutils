# filterutils

Small utilities for building and evaluating filter expressions in Python.

## Features

- Parse simple filter expressions into reusable filter objects
- Evaluate filters against Python objects or dictionaries
- Render filters to parameterized SQL fragments
- Support range expressions such as `10..20` and `10...20`

## Installation

```bash
pip install -e .
```

## Quick start

### Parse a filter expression

```python
from filterutils import FilterExpressionParser

filter_ = FilterExpressionParser.parse("price", ">=10")
```

### Match an object

```python
from filterutils import FilterExpressionParser

filter_ = FilterExpressionParser.parse("quantity", ">=10")
item = {"quantity": 15}

assert filter_.match(item)
```

### Render SQL

```python
from filterutils import FilterExpressionParser

filter_ = FilterExpressionParser.parse("symbol", "AAPL")
sql, parameters = filter_.to_sql()
```

## Notes

- Empty filter trees render to an empty SQL fragment (`""`) and no parameters.
- Range expressions use inclusive bounds for `..` and exclusive bounds for `...`.
- A simple `FilterTree` can be built programmatically with `add_child()`.

## Release checklist

- [ ] Update package version in `pyproject.toml`
- [ ] Ensure tests pass
- [ ] Review public API and documentation
- [ ] Build the distribution package
- [ ] Validate installation in a clean environment
