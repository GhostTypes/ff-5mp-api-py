# AliasPath

**Module:** `pydantic.aliases`

!!! abstract "Usage Documentation"
    [`AliasPath` and `AliasChoices`](../concepts/alias.md#aliaspath-and-aliaschoices)

A data class used by `validation_alias` as a convenience to create aliases.

Attributes:
    path: A list of string or integer aliases.

## Signature

```python
AliasPath(first_arg: 'str', *args: 'str | int') -> 'None'
```

## Methods

### `__init__`

```python
__init__(self, first_arg: 'str', *args: 'str | int') -> 'None'
```

Initialize self.  See help(type(self)) for accurate signature.


### `__replace__`

```python
__replace__(self, /, **changes)
```


### `__repr__`

```python
__repr__(self)
```

Return repr(self).


### `convert_to_aliases`

```python
convert_to_aliases(self) -> 'list[str | int]'
```

Converts arguments to a list of string or integer aliases.

Returns:
    The list of aliases.


### `search_dict_for_path`

```python
search_dict_for_path(self, d: 'dict') -> 'Any'
```

Searches a dictionary for the path specified by the alias.

Returns:
    The value at the specified path, or `PydanticUndefined` if the path is not found.

