# SecretStr

**Module:** `pydantic.types`

A string used for storing sensitive information that you do not want to be visible in logging or tracebacks.

When the secret value is nonempty, it is displayed as `'**********'` instead of the underlying value in
calls to `repr()` and `str()`. If the value _is_ empty, it is displayed as `''`.

```python
from pydantic import BaseModel, SecretStr

class User(BaseModel):
    username: str
    password: SecretStr

user = User(username='scolvin', password='password1')

print(user)
#> username='scolvin' password=SecretStr('**********')
print(user.password.get_secret_value())
#> password1
print((SecretStr('password'), SecretStr('')))
#> (SecretStr('**********'), SecretStr(''))
```

As seen above, by default, [`SecretStr`][pydantic.types.SecretStr] (and [`SecretBytes`][pydantic.types.SecretBytes])
will be serialized as `**********` when serializing to json.

You can use the [`field_serializer`][pydantic.functional_serializers.field_serializer] to dump the
secret as plain-text when serializing to json.

```python
from pydantic import BaseModel, SecretBytes, SecretStr, field_serializer

class Model(BaseModel):
    password: SecretStr
    password_bytes: SecretBytes

    @field_serializer('password', 'password_bytes', when_used='json')
    def dump_secret(self, v):
        return v.get_secret_value()

model = Model(password='IAmSensitive', password_bytes=b'IAmSensitiveBytes')
print(model)
#> password=SecretStr('**********') password_bytes=SecretBytes(b'**********')
print(model.password)
#> **********
print(model.model_dump())
'''
{
    'password': SecretStr('**********'),
    'password_bytes': SecretBytes(b'**********'),
}
'''
print(model.model_dump_json())
#> {"password":"IAmSensitive","password_bytes":"IAmSensitiveBytes"}
```

## Signature

```python
SecretStr(secret_value: 'SecretType') -> 'None'
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

