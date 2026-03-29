# conset

**Module:** `pydantic.types`

## Signature

```python
conset(item_type: 'type[HashableItemType]', *, min_length: 'int | None' = None, max_length: 'int | None' = None) -> 'type[set[HashableItemType]]'
```

## Description

A wrapper around `typing.Set` that allows for additional constraints.

Args:
    item_type: The type of the items in the set.
    min_length: The minimum length of the set.
    max_length: The maximum length of the set.

Returns:
    The wrapped set type.
