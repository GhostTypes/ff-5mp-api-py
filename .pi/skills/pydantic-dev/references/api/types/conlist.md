# conlist

**Module:** `pydantic.types`

## Signature

```python
conlist(item_type: 'type[AnyItemType]', *, min_length: 'int | None' = None, max_length: 'int | None' = None, unique_items: 'bool | None' = None) -> 'type[list[AnyItemType]]'
```

## Description

A wrapper around [`list`][] that adds validation.

Args:
    item_type: The type of the items in the list.
    min_length: The minimum length of the list. Defaults to None.
    max_length: The maximum length of the list. Defaults to None.
    unique_items: Whether the items in the list must be unique. Defaults to None.
        !!! warning Deprecated
            The `unique_items` parameter is deprecated, use `Set` instead.
            See [this issue](https://github.com/pydantic/pydantic-core/issues/296) for more details.

Returns:
    The wrapped list type.
