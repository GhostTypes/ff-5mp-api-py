# AliasChoices

**Module:** `pydantic.aliases`

!!! abstract "Usage Documentation"
    [`AliasPath` and `AliasChoices`](../concepts/alias.md#aliaspath-and-aliaschoices)

A data class used by `validation_alias` as a convenience to create aliases.

Attributes:
    choices: A list containing a string or `AliasPath`.

## Signature

```python
AliasChoices(first_choice: 'str | AliasPath', *choices: 'str | AliasPath') -> 'None'
```

## Methods

### `__init__`

```python
__init__(self, first_choice: 'str | AliasPath', *choices: 'str | AliasPath') -> 'None'
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
convert_to_aliases(self) -> 'list[list[str | int]]'
```

Converts arguments to a list of lists containing string or integer aliases.

Returns:
    The list of aliases.

