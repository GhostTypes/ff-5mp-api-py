# PydanticUndefinedAnnotation

**Module:** `pydantic.errors`

A subclass of `NameError` raised when handling undefined annotations during `CoreSchema` generation.

Attributes:
    name: Name of the error.
    message: Description of the error.

## Signature

```python
PydanticUndefinedAnnotation(name: 'str', message: 'str') -> 'None'
```

## Methods

### `__init__`

```python
__init__(self, name: 'str', message: 'str') -> 'None'
```

Initialize self.  See help(type(self)) for accurate signature.


### `__str__`

```python
__str__(self) -> 'str'
```

Return str(self).


### `from_name_error`

```python
from_name_error(name_error: 'NameError') -> 'Self'
```

Convert a `NameError` to a `PydanticUndefinedAnnotation` error.

Args:
    name_error: `NameError` to be converted.

Returns:
    Converted `PydanticUndefinedAnnotation` error.

