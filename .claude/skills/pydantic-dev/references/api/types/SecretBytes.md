# SecretBytes

**Module:** `pydantic.types`

A bytes used for storing sensitive information that you do not want to be visible in logging or tracebacks.

It displays `b'**********'` instead of the string value on `repr()` and `str()` calls.
When the secret value is nonempty, it is displayed as `b'**********'` instead of the underlying value in
calls to `repr()` and `str()`. If the value _is_ empty, it is displayed as `b''`.

```python
from pydantic import BaseModel, SecretBytes

class User(BaseModel):
    username: str
    password: SecretBytes

user = User(username='scolvin', password=b'password1')
#> username='scolvin' password=SecretBytes(b'**********')
print(user.password.get_secret_value())
#> b'password1'
print((SecretBytes(b'password'), SecretBytes(b'')))
#> (SecretBytes(b'**********'), SecretBytes(b''))
```

## Signature

```python
SecretBytes(secret_value: 'SecretType') -> 'None'
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


### `__len__`

```python
__len__(self) -> 'int'
```


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

