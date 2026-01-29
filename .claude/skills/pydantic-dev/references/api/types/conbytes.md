# conbytes

**Module:** `pydantic.types`

## Signature

```python
conbytes(*, min_length: 'int | None' = None, max_length: 'int | None' = None, strict: 'bool | None' = None) -> 'type[bytes]'
```

## Description

A wrapper around `bytes` that allows for additional constraints.

Args:
    min_length: The minimum length of the bytes.
    max_length: The maximum length of the bytes.
    strict: Whether to validate the bytes in strict mode.

Returns:
    The wrapped bytes type.
