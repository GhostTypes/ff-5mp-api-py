# EncodedBytes

**Module:** `pydantic.types`

A bytes type that is encoded and decoded using the specified encoder.

`EncodedBytes` needs an encoder that implements `EncoderProtocol` to operate.

```python
from typing import Annotated

from pydantic import BaseModel, EncodedBytes, EncoderProtocol, ValidationError

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

MyEncodedBytes = Annotated[bytes, EncodedBytes(encoder=MyEncoder)]

class Model(BaseModel):
    my_encoded_bytes: MyEncodedBytes

# Initialize the model with encoded data
m = Model(my_encoded_bytes=b'**encoded**: some bytes')

# Access decoded value
print(m.my_encoded_bytes)
#> b'some bytes'

# Serialize into the encoded form
print(m.model_dump())
#> {'my_encoded_bytes': b'**encoded**: some bytes'}

# Validate encoded data
try:
    Model(my_encoded_bytes=b'**undecodable**')
except ValidationError as e:
    print(e)
    '''
    1 validation error for Model
    my_encoded_bytes
      Value error, Cannot decode data [type=value_error, input_value=b'**undecodable**', input_type=bytes]
    '''
```

## Signature

```python
EncodedBytes(encoder: 'type[EncoderProtocol]') -> None
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


### `decode`

```python
decode(self, data: 'bytes', _: 'core_schema.ValidationInfo') -> 'bytes'
```

Decode the data using the specified encoder.

Args:
    data: The data to decode.

Returns:
    The decoded data.


### `encode`

```python
encode(self, value: 'bytes') -> 'bytes'
```

Encode the data using the specified encoder.

Args:
    value: The data to encode.

Returns:
    The encoded data.

