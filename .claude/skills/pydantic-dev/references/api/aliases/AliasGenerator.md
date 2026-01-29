# AliasGenerator

**Module:** `pydantic.aliases`

!!! abstract "Usage Documentation"
    [Using an `AliasGenerator`](../concepts/alias.md#using-an-aliasgenerator)

A data class used by `alias_generator` as a convenience to create various aliases.

Attributes:
    alias: A callable that takes a field name and returns an alias for it.
    validation_alias: A callable that takes a field name and returns a validation alias for it.
    serialization_alias: A callable that takes a field name and returns a serialization alias for it.

## Signature

```python
AliasGenerator(alias: 'Callable[[str], str] | None' = None, validation_alias: 'Callable[[str], str | AliasPath | AliasChoices] | None' = None, serialization_alias: 'Callable[[str], str] | None' = None) -> None
```

## Methods

### `__init__`

```python
__init__(self, alias: 'Callable[[str], str] | None' = None, validation_alias: 'Callable[[str], str | AliasPath | AliasChoices] | None' = None, serialization_alias: 'Callable[[str], str] | None' = None) -> None
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


### `generate_aliases`

```python
generate_aliases(self, field_name: 'str') -> 'tuple[str | None, str | AliasPath | AliasChoices | None, str | None]'
```

Generate `alias`, `validation_alias`, and `serialization_alias` for a field.

Returns:
    A tuple of three aliases - validation, alias, and serialization.

