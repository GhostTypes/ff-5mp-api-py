# WrapValidator

**Module:** `pydantic.functional_validators`

!!! abstract "Usage Documentation"
    [field *wrap* validators](../concepts/validators.md#field-wrap-validator)

A metadata class that indicates that a validation should be applied **around** the inner validation logic.

Attributes:
    func: The validator function.
    json_schema_input_type: The input type used to generate the appropriate
        JSON Schema (in validation mode). The actual input type is `Any`.

```python
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ValidationError, WrapValidator

def validate_timestamp(v, handler):
    if v == 'now':
        # we don't want to bother with further validation, just return the new value
        return datetime.now()
    try:
        return handler(v)
    except ValidationError:
        # validation failed, in this case we want to return a default value
        return datetime(2000, 1, 1)

MyTimestamp = Annotated[datetime, WrapValidator(validate_timestamp)]

class Model(BaseModel):
    a: MyTimestamp

print(Model(a='now').a)
#> 2032-01-02 03:04:05.000006
print(Model(a='invalid').a)
#> 2000-01-01 00:00:00
```

## Signature

```python
WrapValidator(func: 'core_schema.NoInfoWrapValidatorFunction | core_schema.WithInfoWrapValidatorFunction', json_schema_input_type: 'Any' = PydanticUndefined) -> None
```

## Methods

### `__get_pydantic_core_schema__`

```python
__get_pydantic_core_schema__(self, source_type: 'Any', handler: 'GetCoreSchemaHandler') -> 'core_schema.CoreSchema'
```


### `__init__`

```python
__init__(self, func: 'core_schema.NoInfoWrapValidatorFunction | core_schema.WithInfoWrapValidatorFunction', json_schema_input_type: 'Any' = PydanticUndefined) -> None
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


### `__setstate__`

```python
__setstate__(self, state)
```

