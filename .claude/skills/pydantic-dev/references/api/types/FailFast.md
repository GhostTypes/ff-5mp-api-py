# FailFast

**Module:** `pydantic.types`

A `FailFast` annotation can be used to specify that validation should stop at the first error.

This can be useful when you want to validate a large amount of data and you only need to know if it's valid or not.

You might want to enable this setting if you want to validate your data faster (basically, if you use this,
validation will be more performant with the caveat that you get less information).

```python
from typing import Annotated

from pydantic import BaseModel, FailFast, ValidationError

class Model(BaseModel):
    x: Annotated[list[int], FailFast()]

# This will raise a single error for the first invalid value and stop validation
try:
    obj = Model(x=[1, 2, 'a', 4, 5, 'b', 7, 8, 9, 'c'])
except ValidationError as e:
    print(e)
    '''
    1 validation error for Model
    x.2
      Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='a', input_type=str]
    '''
```

## Signature

```python
FailFast(fail_fast: 'bool' = True) -> None
```

## Methods

### `__init__`

```python
__init__(self, fail_fast: 'bool' = True) -> None
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

