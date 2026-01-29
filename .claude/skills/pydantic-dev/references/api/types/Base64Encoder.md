# Base64Encoder

**Module:** `pydantic.types`

Standard (non-URL-safe) Base64 encoder.

## Signature

```python
Base64Encoder(*args, **kwargs)
```

## Methods

### `__init__`

```python
__init__(self, *args, **kwargs)
```


### `decode`

```python
decode(data: 'bytes') -> 'bytes'
```

Decode the data from base64 encoded bytes to original bytes data.

Args:
    data: The data to decode.

Returns:
    The decoded data.


### `encode`

```python
encode(value: 'bytes') -> 'bytes'
```

Encode the data from bytes to a base64 encoded bytes.

Args:
    value: The data to encode.

Returns:
    The encoded data.


### `get_json_format`

```python
get_json_format() -> "Literal['base64']"
```

Get the JSON format for the encoded data.

Returns:
    The JSON format for the encoded data.

