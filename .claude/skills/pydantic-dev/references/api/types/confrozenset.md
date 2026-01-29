# confrozenset

**Module:** `pydantic.types`

## Signature

```python
confrozenset(item_type: 'type[HashableItemType]', *, min_length: 'int | None' = None, max_length: 'int | None' = None) -> 'type[frozenset[HashableItemType]]'
```

## Description

A wrapper around `typing.FrozenSet` that allows for additional constraints.

Args:
    item_type: The type of the items in the frozenset.
    min_length: The minimum length of the frozenset.
    max_length: The maximum length of the frozenset.

Returns:
    The wrapped frozenset type.
