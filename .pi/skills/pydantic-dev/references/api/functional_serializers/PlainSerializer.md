# PlainSerializer

**Module:** `pydantic.functional_serializers`

Plain serializers use a function to modify the output of serialization.

This is particularly helpful when you want to customize the serialization for annotated types.
Consider an input of `list`, which will be serialized into a space-delimited string.

```python
from typing import Annotated

from pydantic import BaseModel, PlainSerializer

CustomStr = Annotated[
    list, PlainSerializer(lambda x: ' '.join(x), return_type=str)
]

class StudentModel(BaseModel):
    courses: CustomStr

student = StudentModel(courses=['Math', 'Chemistry', 'English'])
print(student.model_dump())
#> {'courses': 'Math Chemistry English'}
```

Attributes:
    func: The serializer function.
    return_type: The return type for the function. If omitted it will be inferred from the type annotation.
    when_used: Determines when this serializer should be used. Accepts a string with values `'always'`,
        `'unless-none'`, `'json'`, and `'json-unless-none'`. Defaults to 'always'.

## Signature

```python
PlainSerializer(func: 'core_schema.SerializerFunction', return_type: 'Any' = PydanticUndefined, when_used: 'WhenUsed' = 'always') -> None
```

## Methods

### `__get_pydantic_core_schema__`

```python
__get_pydantic_core_schema__(self, source_type: 'Any', handler: 'GetCoreSchemaHandler') -> 'core_schema.CoreSchema'
```

Gets the Pydantic core schema.

Args:
    source_type: The source type.
    handler: The `GetCoreSchemaHandler` instance.

Returns:
    The Pydantic core schema.


### `__init__`

```python
__init__(self, func: 'core_schema.SerializerFunction', return_type: 'Any' = PydanticUndefined, when_used: 'WhenUsed' = 'always') -> None
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

