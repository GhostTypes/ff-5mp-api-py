# GetPydanticSchema

**Module:** `pydantic.types`

!!! abstract "Usage Documentation"
    [Using `GetPydanticSchema` to Reduce Boilerplate](../concepts/types.md#using-getpydanticschema-to-reduce-boilerplate)

A convenience class for creating an annotation that provides pydantic custom type hooks.

This class is intended to eliminate the need to create a custom "marker" which defines the
 `__get_pydantic_core_schema__` and `__get_pydantic_json_schema__` custom hook methods.

For example, to have a field treated by type checkers as `int`, but by pydantic as `Any`, you can do:
```python
from typing import Annotated, Any

from pydantic import BaseModel, GetPydanticSchema

HandleAsAny = GetPydanticSchema(lambda _s, h: h(Any))

class Model(BaseModel):
    x: Annotated[int, HandleAsAny]  # pydantic sees `x: Any`

print(repr(Model(x='abc').x))
#> 'abc'
```

## Signature

```python
GetPydanticSchema(get_pydantic_core_schema: 'Callable[[Any, GetCoreSchemaHandler], CoreSchema] | None' = None, get_pydantic_json_schema: 'Callable[[Any, GetJsonSchemaHandler], JsonSchemaValue] | None' = None) -> None
```

## Methods

### `__getattr__`

```python
__getattr__(self, item: 'str') -> 'Any'
```

Use this rather than defining `__get_pydantic_core_schema__` etc. to reduce the number of nested calls.


### `__init__`

```python
__init__(self, get_pydantic_core_schema: 'Callable[[Any, GetCoreSchemaHandler], CoreSchema] | None' = None, get_pydantic_json_schema: 'Callable[[Any, GetJsonSchemaHandler], JsonSchemaValue] | None' = None) -> None
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

