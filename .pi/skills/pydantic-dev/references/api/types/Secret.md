# Secret

**Module:** `pydantic.types`

A generic base class used for defining a field with sensitive information that you do not want to be visible in logging or tracebacks.

You may either directly parametrize `Secret` with a type, or subclass from `Secret` with a parametrized type. The benefit of subclassing
is that you can define a custom `_display` method, which will be used for `repr()` and `str()` methods. The examples below demonstrate both
ways of using `Secret` to create a new secret type.

1. Directly parametrizing `Secret` with a type:

```python
from pydantic import BaseModel, Secret

SecretBool = Secret[bool]

class Model(BaseModel):
    secret_bool: SecretBool

m = Model(secret_bool=True)
print(m.model_dump())
#> {'secret_bool': Secret('**********')}

print(m.model_dump_json())
#> {"secret_bool":"**********"}

print(m.secret_bool.get_secret_value())
#> True
```

2. Subclassing from parametrized `Secret`:

```python
from datetime import date

from pydantic import BaseModel, Secret

class SecretDate(Secret[date]):
    def _display(self) -> str:
        return '****/**/**'

class Model(BaseModel):
    secret_date: SecretDate

m = Model(secret_date=date(2022, 1, 1))
print(m.model_dump())
#> {'secret_date': SecretDate('****/**/**')}

print(m.model_dump_json())
#> {"secret_date":"****/**/**"}

print(m.secret_date.get_secret_value())
#> 2022-01-01
```

The value returned by the `_display` method will be used for `repr()` and `str()`.

You can enforce constraints on the underlying type through annotations:
For example:

```python
from typing import Annotated

from pydantic import BaseModel, Field, Secret, ValidationError

SecretPosInt = Secret[Annotated[int, Field(gt=0, strict=True)]]

class Model(BaseModel):
    sensitive_int: SecretPosInt

m = Model(sensitive_int=42)
print(m.model_dump())
#> {'sensitive_int': Secret('**********')}

try:
    m = Model(sensitive_int=-42)  # (1)!
except ValidationError as exc_info:
    print(exc_info.errors(include_url=False, include_input=False))
    '''
    [
        {
            'type': 'greater_than',
            'loc': ('sensitive_int',),
            'msg': 'Input should be greater than 0',
            'ctx': {'gt': 0},
        }
    ]
    '''

try:
    m = Model(sensitive_int='42')  # (2)!
except ValidationError as exc_info:
    print(exc_info.errors(include_url=False, include_input=False))
    '''
    [
        {
            'type': 'int_type',
            'loc': ('sensitive_int',),
            'msg': 'Input should be a valid integer',
        }
    ]
    '''
```

1. The input value is not greater than 0, so it raises a validation error.
2. The input value is not an integer, so it raises a validation error because the `SecretPosInt` type has strict mode enabled.

## Signature

```python
Secret(secret_value: 'SecretType') -> 'None'
```

## Methods

### `__get_pydantic_core_schema__`

```python
__get_pydantic_core_schema__(source: 'type[Any]', handler: 'GetCoreSchemaHandler') -> 'core_schema.CoreSchema'
```


### `__init__`

```python
__init__(self, secret_value: 'SecretType') -> 'None'
```

Initialize self.  See help(type(self)) for accurate signature.


### `__repr__`

```python
__repr__(self) -> 'str'
```

Return repr(self).


### `__str__`

```python
__str__(self) -> 'str'
```

Return str(self).


### `get_secret_value`

```python
get_secret_value(self) -> 'SecretType'
```

Get the secret value.

Returns:
    The secret value.

