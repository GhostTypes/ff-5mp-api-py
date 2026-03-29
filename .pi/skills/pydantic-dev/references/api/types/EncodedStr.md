# EncodedStr

**Module:** `pydantic.types`

A str type that is encoded and decoded using the specified encoder.

`EncodedStr` needs an encoder that implements `EncoderProtocol` to operate.

```python
from typing import Annotated

from pydantic import BaseModel, EncodedStr, EncoderProtocol, ValidationError

class MyEncoder(EncoderProtocol):
    @classmethod
    def decode(cls, data: bytes) -> bytes:
        if data == b'**undecodable**':
            raise ValueError('Cannot decode data')
        return data[13:]

    @classmethod
    def encode(cls, value: bytes) -> bytes:
        return b'**encoded**: ' + value

    @classmethod
    def get_json_format(cls) -> str:
        return 'my-encoder'

MyEncodedStr = Annotated[str, EncodedStr(encoder=MyEncoder)]

class Model(BaseModel):
    my_encoded_str: MyEncodedStr

# Initialize the model with encoded data
m = Model(my_encoded_str='**encoded**: some str')

# Access decoded value
print(m.my_encoded_str)
#> some str

# Serialize into the encoded form
print(m.model_dump())
#> {'my_encoded_str': '**encoded**: some str'}

# Validate encoded data
try:
    Model(my_encoded_str='**undecodable**')
except ValidationError as e:
    print(e)
    '''
    1 validation error for Model
    my_encoded_str
      Value error, Cannot decode data [type=value_error, input_value='**undecodable**', input_type=str]
    '''
```

## Signature

```python
EncodedStr(encoder: 'type[EncoderProtocol]') -> None
```

## Methods

### `__get_pydantic_core_schema__`

```python
__get_pydantic_core_schema__(self, source: 'type[Any]', handler: 'GetCoreSchemaHandler') -> 'core_schema.CoreSchema'
```


### `__get_pydantic_json_schema__`

```python
__get_pydantic_json_schema__(self, core_schema: 'core_schema.CoreSchema', handler: 'GetJsonSchemaHandler') -> 'JsonSchemaValue'
```


### `__init__`

```python
__init__(self, encoder: 'type[EncoderProtocol]') -> None
```

Initialize self.  See help(type(self)) for accurate signature.


### `__replace__`

```python
__replace__(self, /, **changes)
```


### `__repr__`

```python
__repr__(self)
```

Return repr(self).


### `decode_str`

```python
decode_str(self, data: 'str', _: 'core_schema.ValidationInfo') -> 'str'
```

Decode the data using the specified encoder.

Args:
    data: The data to decode.

Returns:
    The decoded data.


### `encode_str`

```python
encode_str(self, value: 'str') -> 'str'
```

Encode the data using the specified encoder.

Args:
    value: The data to encode.

Returns:
    The encoded data.

