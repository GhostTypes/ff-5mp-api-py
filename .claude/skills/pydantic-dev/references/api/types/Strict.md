# Strict

**Module:** `pydantic.types`

!!! abstract "Usage Documentation"
    [Strict Mode with `Annotated` `Strict`](../concepts/strict_mode.md#strict-mode-with-annotated-strict)

A field metadata class to indicate that a field should be validated in strict mode.
Use this class as an annotation via [`Annotated`](https://docs.python.org/3/library/typing.html#typing.Annotated), as seen below.

Attributes:
    strict: Whether to validate the field in strict mode.

Example:
    ```python
    from typing import Annotated

    from pydantic.types import Strict

    StrictBool = Annotated[bool, Strict()]
    ```

## Signature

```python
Strict(strict: 'bool' = True) -> None
```

## Methods

### `__init__`

```python
__init__(self, strict: 'bool' = True) -> None
```

Initialize self.  See help(type(self)) for accurate signature.


### `__pretty__`

```python
__pretty__(self, fmt: 'Callable[[Any], Any]', **kwargs: 'Any') -> 'Generator[Any]'
```

Used by devtools (https://python-devtools.helpmanual.io/) to pretty print objects.


### `__replace__`

```python
__replace__(self, /, **changes)
```


### `__repr__`

```python
__repr__(self)
```

Return repr(self).


### `__repr_args__`

```python
__repr_args__(self) -> 'ReprArgs'
```

Returns the attributes to show in __str__, __repr__, and __pretty__ this is generally overridden.

Can either return:
* name - value pairs, e.g.: `[('foo_name', 'foo'), ('bar_name', ['b', 'a', 'r'])]`
* or, just values, e.g.: `[(None, 'foo'), (None, ['b', 'a', 'r'])]`


### `__repr_name__`

```python
__repr_name__(self) -> 'str'
```

Name of the instance's class, used in __repr__.


### `__repr_recursion__`

```python
__repr_recursion__(self, object: 'Any') -> 'str'
```

Returns the string representation of a recursive object.


### `__repr_str__`

```python
__repr_str__(self, join_str: 'str') -> 'str'
```


### `__rich_repr__`

```python
__rich_repr__(self) -> 'RichReprResult'
```

Used by Rich (https://rich.readthedocs.io/en/stable/pretty.html) to pretty print objects.


### `__str__`

```python
__str__(self) -> 'str'
```

Return str(self).

