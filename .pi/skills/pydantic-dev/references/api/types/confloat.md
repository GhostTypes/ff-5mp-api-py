# confloat

**Module:** `pydantic.types`

## Signature

```python
confloat(*, strict: 'bool | None' = None, gt: 'float | None' = None, ge: 'float | None' = None, lt: 'float | None' = None, le: 'float | None' = None, multiple_of: 'float | None' = None, allow_inf_nan: 'bool | None' = None) -> 'type[float]'
```

## Description

!!! warning "Discouraged"
    This function is **discouraged** in favor of using
    [`Annotated`](https://docs.python.org/3/library/typing.html#typing.Annotated) with
    [`Field`][pydantic.fields.Field] instead.

    This function will be **deprecated** in Pydantic 3.0.

    The reason is that `confloat` returns a type, which doesn't play well with static analysis tools.

    === ":x: Don't do this"
        ```python
        from pydantic import BaseModel, confloat

        class Foo(BaseModel):
            bar: confloat(strict=True, gt=0)
        ```

    === ":white_check_mark: Do this"
        ```python
        from typing import Annotated

        from pydantic import BaseModel, Field

        class Foo(BaseModel):
            bar: Annotated[float, Field(strict=True, gt=0)]
        ```

A wrapper around `float` that allows for additional constraints.

Args:
    strict: Whether to validate the float in strict mode.
    gt: The value must be greater than this.
    ge: The value must be greater than or equal to this.
    lt: The value must be less than this.
    le: The value must be less than or equal to this.
    multiple_of: The value must be a multiple of this.
    allow_inf_nan: Whether to allow `-inf`, `inf`, and `nan`.

Returns:
    The wrapped float type.

```python
from pydantic import BaseModel, ValidationError, confloat

class ConstrainedExample(BaseModel):
    constrained_float: confloat(gt=1.0)

m = ConstrainedExample(constrained_float=1.1)
print(repr(m))
#> ConstrainedExample(constrained_float=1.1)

try:
    ConstrainedExample(constrained_float=0.9)
except ValidationError as e:
    print(e.errors())
    '''
    [
        {
            'type': 'greater_than',
            'loc': ('constrained_float',),
            'msg': 'Input should be greater than 1',
            'input': 0.9,
            'ctx': {'gt': 1.0},
            'url': 'https://errors.pydantic.dev/2/v/greater_than',
        }
    ]
    '''
```
