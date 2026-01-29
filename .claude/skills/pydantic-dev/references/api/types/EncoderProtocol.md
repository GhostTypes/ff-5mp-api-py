# EncoderProtocol

**Module:** `pydantic.types`

Protocol for encoding and decoding data to and from bytes.

## Signature

```python
EncoderProtocol(*args, **kwargs)
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

Decode the data using the encoder.

Args:
    data: The data to decode.

Returns:
    The decoded data.


### `encode`

```python
encode(value: 'bytes') -> 'bytes'
```

Encode the data using the encoder.

Args:
    value: The data to encode.

Returns:
    The encoded data.


### `get_json_format`

```python
get_json_format() -> 'str'
```

Get the JSON format for the encoded data.

Returns:
    The JSON format for the encoded data.

