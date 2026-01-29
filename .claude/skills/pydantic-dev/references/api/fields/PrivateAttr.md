# PrivateAttr

**Module:** `pydantic.fields`

## Signature

```python
PrivateAttr(default: 'Any' = PydanticUndefined, *, default_factory: 'Callable[[], Any] | None' = None, init: 'Literal[False]' = False) -> 'Any'
```

## Description

!!! abstract "Usage Documentation"
    [Private Model Attributes](../concepts/models.md#private-model-attributes)

Indicates that an attribute is intended for private use and not handled during normal validation/serialization.

Private attributes are not validated by Pydantic, so it's up to you to ensure they are used in a type-safe manner.

Private attributes are stored in `__private_attributes__` on the model.

Args:
    default: The attribute's default value. Defaults to Undefined.
    default_factory: Callable that will be
        called when a default value is needed for this attribute.
        If both `default` and `default_factory` are set, an error will be raised.
    init: Whether the attribute should be included in the constructor of the dataclass. Always `False`.

Returns:
    An instance of [`ModelPrivateAttr`][pydantic.fields.ModelPrivateAttr] class.

Raises:
    ValueError: If both `default` and `default_factory` are set.
