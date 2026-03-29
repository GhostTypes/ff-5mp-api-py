# condate

**Module:** `pydantic.types`

## Signature

```python
condate(*, strict: 'bool | None' = None, gt: 'date | None' = None, ge: 'date | None' = None, lt: 'date | None' = None, le: 'date | None' = None) -> 'type[date]'
```

## Description

A wrapper for date that adds constraints.

Args:
    strict: Whether to validate the date value in strict mode. Defaults to `None`.
    gt: The value must be greater than this. Defaults to `None`.
    ge: The value must be greater than or equal to this. Defaults to `None`.
    lt: The value must be less than this. Defaults to `None`.
    le: The value must be less than or equal to this. Defaults to `None`.

Returns:
    A date type with the specified constraints.
