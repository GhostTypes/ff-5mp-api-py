# parse_mypy_version

**Module:** `pydantic.version`

## Signature

```python
parse_mypy_version(version: 'str') -> 'tuple[int, int, int]'
```

## Description

Parse `mypy` string version to a 3-tuple of ints.

It parses normal version like `1.11.0` and extra info followed by a `+` sign
like `1.11.0+dev.d6d9d8cd4f27c52edac1f537e236ec48a01e54cb.dirty`.

Args:
    version: The mypy version string.

Returns:
    A triple of ints, e.g. `(1, 11, 0)`.
