# NameEmail

**Module:** `pydantic.networks`

Info:
    To use this type, you need to install the optional
    [`email-validator`](https://github.com/JoshData/python-email-validator) package:

    ```bash
    pip install email-validator
    ```

Validate a name and email address combination, as specified by
[RFC 5322](https://datatracker.ietf.org/doc/html/rfc5322#section-3.4).

The `NameEmail` has two properties: `name` and `email`.
In case the `name` is not provided, it's inferred from the email address.

```python
from pydantic import BaseModel, NameEmail

class User(BaseModel):
    email: NameEmail

user = User(email='Fred Bloggs <fred.bloggs@example.com>')
print(user.email)
#> Fred Bloggs <fred.bloggs@example.com>
print(user.email.name)
#> Fred Bloggs

user = User(email='fred.bloggs@example.com')
print(user.email)
#> fred.bloggs <fred.bloggs@example.com>
print(user.email.name)
#> fred.bloggs
```

## Signature

```python
NameEmail(name: 'str', email: 'str')
```

## Methods

### `__get_pydantic_core_schema__`

```python
__get_pydantic_core_schema__(_source: 'type[Any]', _handler: 'GetCoreSchemaHandler') -> 'core_schema.CoreSchema'
```


### `__get_pydantic_json_schema__`

```python
__get_pydantic_json_schema__(core_schema: 'core_schema.CoreSchema', handler: '_schema_generation_shared.GetJsonSchemaHandler') -> 'JsonSchemaValue'
```


### `__init__`

```python
__init__(self, name: 'str', email: 'str')
```

Initialize self.  See help(type(self)) for accurate signature.


### `__pretty__`

```python
__pretty__(self, fmt: 'Callable[[Any], Any]', **kwargs: 'Any') -> 'Generator[Any]'
```

Used by devtools (https://python-devtools.helpmanual.io/) to pretty print objects.


### `__repr__`

```python
__repr__(self) -> 'str'
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

