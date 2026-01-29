# PydanticErrorMixin

**Module:** `pydantic.errors`

A mixin class for common functionality shared by all Pydantic-specific errors.

Attributes:
    message: A message describing the error.
    code: An optional error code from PydanticErrorCodes enum.

## Signature

```python
PydanticErrorMixin(message: 'str', *, code: 'PydanticErrorCodes | None') -> 'None'
```

## Methods

### `__init__`

```python
__init__(self, message: 'str', *, code: 'PydanticErrorCodes | None') -> 'None'
```

Initialize self.  See help(type(self)) for accurate signature.


### `__str__`

```python
__str__(self) -> 'str'
```

Return str(self).

