# constr

**Module:** `pydantic.types`

## Signature

```python
constr(*, strip_whitespace: 'bool | None' = None, to_upper: 'bool | None' = None, to_lower: 'bool | None' = None, strict: 'bool | None' = None, min_length: 'int | None' = None, max_length: 'int | None' = None, pattern: 'str | Pattern[str] | None' = None) -> 'type[str]'
```

## Description

!!! warning "Discouraged"
    This function is **discouraged** in favor of using
    [`Annotated`](https://docs.python.org/3/library/typing.html#typing.Annotated) with
    [`StringConstraints`][pydantic.types.StringConstraints] instead.

    This function will be **deprecated** in Pydantic 3.0.

    The reason is that `constr` returns a type, which doesn't play well with static analysis tools.

    === ":x: Don't do this"
        ```python
        from pydantic import BaseModel, constr

        class Foo(BaseModel):
            bar: constr(strip_whitespace=True, to_upper=True, pattern=r'^[A-Z]+$')
        ```

    === ":white_check_mark: Do this"
        ```python
        from typing import Annotated

        from pydantic import BaseModel, StringConstraints

        class Foo(BaseModel):
            bar: Annotated[
                str,
                StringConstraints(
                    strip_whitespace=True, to_upper=True, pattern=r'^[A-Z]+$'
                ),
            ]
        ```

A wrapper around `str` that allows for additional constraints.

```python
from pydantic import BaseModel, constr

class Foo(BaseModel):
    bar: constr(strip_whitespace=True, to_upper=True)

foo = Foo(bar='  hello  ')
print(foo)
#> bar='HELLO'
```

Args:
    strip_whitespace: Whether to remove leading and trailing whitespace.
    to_upper: Whether to turn all characters to uppercase.
    to_lower: Whether to turn all characters to lowercase.
    strict: Whether to validate the string in strict mode.
    min_length: The minimum length of the string.
    max_length: The maximum length of the string.
    pattern: A regex pattern to validate the string against.

Returns:
    The wrapped string type.
