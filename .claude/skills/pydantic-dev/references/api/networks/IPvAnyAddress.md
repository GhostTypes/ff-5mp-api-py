# IPvAnyAddress

**Module:** `pydantic.networks`

Validate an IPv4 or IPv6 address.

```python
from pydantic import BaseModel
from pydantic.networks import IPvAnyAddress

class IpModel(BaseModel):
    ip: IPvAnyAddress

print(IpModel(ip='127.0.0.1'))
#> ip=IPv4Address('127.0.0.1')

try:
    IpModel(ip='http://www.example.com')
except ValueError as e:
    print(e.errors())
    '''
    [
        {
            'type': 'ip_any_address',
            'loc': ('ip',),
            'msg': 'value is not a valid IPv4 or IPv6 address',
            'input': 'http://www.example.com',
        }
    ]
    '''
```

## Signature

```python
IPvAnyAddress(value: 'Any') -> 'IPvAnyAddressType'
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

