# StringConstraints

**Module:** `pydantic.types`

!!! abstract "Usage Documentation"
    [String types](./standard_library_types.md#strings)

A field metadata class to apply constraints to `str` types.
Use this class as an annotation via [`Annotated`](https://docs.python.org/3/library/typing.html#typing.Annotated), as seen below.

Attributes:
    strip_whitespace: Whether to remove leading and trailing whitespace.
    to_upper: Whether to convert the string to uppercase.
    to_lower: Whether to convert the string to lowercase.
    strict: Whether to validate the string in strict mode.
    min_length: The minimum length of the string.
    max_length: The maximum length of the string.
    pattern: A regex pattern that the string must match.

Example:
    ```python
    from typing import Annotated

    from pydantic.types import StringConstraints

    ConstrainedStr = Annotated[str, StringConstraints(min_length=1, max_length=10)]
    ```

## Signature

```python
StringConstraints(strip_whitespace: 'bool | None' = None, to_upper: 'bool | None' = None, to_lower: 'bool | None' = None, strict: 'bool | None' = None, min_length: 'int | None' = None, max_length: 'int | None' = None, pattern: 'str | Pattern[str] | None' = None) -> None
```

## Methods

### `__init__`

```python
__init__(self, strip_whitespace: 'bool | None' = None, to_upper: 'bool | None' = None, to_lower: 'bool | None' = None, strict: 'bool | None' = None, min_length: 'int | None' = None, max_length: 'int | None' = None, pattern: 'str | Pattern[str] | None' = None) -> None
```

Initialize self.  See help(type(self)) for accurate signature.


### `__iter__`

```python
__iter__(self) -> 'Iterator[BaseMetadata]'
```


### `__replace__`

```python
__replace__(self, /, **changes)
```


### `__repr__`

```python
__repr__(self)
```

Return repr(self).


## Properties

### `__is_annotated_types_grouped_metadata__`

