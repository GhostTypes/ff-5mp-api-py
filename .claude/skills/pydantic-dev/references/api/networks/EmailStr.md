# EmailStr

**Module:** `pydantic.networks`

Info:
    To use this type, you need to install the optional
    [`email-validator`](https://github.com/JoshData/python-email-validator) package:

    ```bash
    pip install email-validator
    ```

Validate email addresses.

```python
from pydantic import BaseModel, EmailStr

class Model(BaseModel):
    email: EmailStr

print(Model(email='contact@mail.com'))
#> email='contact@mail.com'
```

## Signature

```python
EmailStr()
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

