# conint

**Module:** `pydantic.types`

## Signature

```python
conint(*, strict: 'bool | None' = None, gt: 'int | None' = None, ge: 'int | None' = None, lt: 'int | None' = None, le: 'int | None' = None, multiple_of: 'int | None' = None) -> 'type[int]'
```

## Description

!!! warning "Discouraged"
    This function is **discouraged** in favor of using
    [`Annotated`](https://docs.python.org/3/library/typing.html#typing.Annotated) with
    [`Field`][pydantic.fields.Field] instead.

    This function will be **deprecated** in Pydantic 3.0.

    The reason is that `conint` returns a type, which doesn't play well with static analysis tools.

    === ":x: Don't do this"
        ```python
        from pydantic import BaseModel, conint

        class Foo(BaseModel):
            bar: conint(strict=True, gt=0)
        ```

    === ":white_check_mark: Do this"
        ```python
        from typing import Annotated

        from pydantic import BaseModel, Field

        class Foo(BaseModel):
            bar: Annotated[int, Field(strict=True, gt=0)]
        ```

A wrapper around `int` that allows for additional constraints.

Args:
    strict: Whether to validate the integer in strict mode. Defaults to `None`.
    gt: The value must be greater than this.
    ge: The value must be greater than or equal to this.
    lt: The value must be less than this.
    le: The value must be less than or equal to this.
    multiple_of: The value must be a multiple of this.

Returns:
    The wrapped integer type.

```python
from pydantic import BaseModel, ValidationError, conint

class ConstrainedExample(BaseModel):
    constrained_int: conint(gt=1)

m = ConstrainedExample(constrained_int=2)
print(repr(m))
#> ConstrainedExample(constrained_int=2)

try:
    ConstrainedExample(constrained_int=0)
except ValidationError as e:
    print(e.errors())
    '''
    [
        {
            'type': 'greater_than',
            'loc': ('constrained_int',),
            'msg': 'Input should be greater than 1',
            'input': 0,
            'ctx': {'gt': 1},
            'url': 'https://errors.pydantic.dev/2/v/greater_than',
        }
    ]
    '''
```
