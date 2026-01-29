# ComputedFieldInfo

**Module:** `pydantic.fields`

A container for data from `@computed_field` so that we can access it while building the pydantic-core schema.

Attributes:
    decorator_repr: A class variable representing the decorator string, '@computed_field'.
    wrapped_property: The wrapped computed field property.
    return_type: The type of the computed field property's return value.
    alias: The alias of the property to be used during serialization.
    alias_priority: The priority of the alias. This affects whether an alias generator is used.
    title: Title of the computed field to include in the serialization JSON schema.
    field_title_generator: A callable that takes a field name and returns title for it.
    description: Description of the computed field to include in the serialization JSON schema.
    deprecated: A deprecation message, an instance of `warnings.deprecated` or the `typing_extensions.deprecated` backport,
        or a boolean. If `True`, a default deprecation message will be emitted when accessing the field.
    examples: Example values of the computed field to include in the serialization JSON schema.
    json_schema_extra: A dict or callable to provide extra JSON schema properties.
    repr: A boolean indicating whether to include the field in the __repr__ output.

## Signature

```python
ComputedFieldInfo(wrapped_property: 'property', return_type: 'Any', alias: 'str | None', alias_priority: 'int | None', title: 'str | None', field_title_generator: 'Callable[[str, ComputedFieldInfo], str] | None', description: 'str | None', deprecated: 'Deprecated | str | bool | None', examples: 'list[Any] | None', json_schema_extra: 'JsonDict | Callable[[JsonDict], None] | None', repr: 'bool') -> None
```

## Methods

### `__init__`

```python
__init__(self, wrapped_property: 'property', return_type: 'Any', alias: 'str | None', alias_priority: 'int | None', title: 'str | None', field_title_generator: 'Callable[[str, ComputedFieldInfo], str] | None', description: 'str | None', deprecated: 'Deprecated | str | bool | None', examples: 'list[Any] | None', json_schema_extra: 'JsonDict | Callable[[JsonDict], None] | None', repr: 'bool') -> None
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


## Properties

### `deprecation_message`

The deprecation message to be emitted, or `None` if not set.

