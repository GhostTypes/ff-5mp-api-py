# MySQLDsn

**Module:** `pydantic.networks`

A type that will accept any MySQL DSN.

* User info required
* TLD not required
* Host not required

## Signature

```python
MySQLDsn(url: 'str | _CoreUrl | _BaseUrl') -> 'None'
```

## Methods

### `__deepcopy__`

```python
__deepcopy__(self, memo: 'dict') -> 'Self'
```


### `__get_pydantic_core_schema__`

```python
__get_pydantic_core_schema__(source: 'type[_BaseUrl]', handler: 'GetCoreSchemaHandler') -> 'core_schema.CoreSchema'
```


### `__get_pydantic_json_schema__`

```python
__get_pydantic_json_schema__(core_schema: 'core_schema.CoreSchema', handler: '_schema_generation_shared.GetJsonSchemaHandler') -> 'JsonSchemaValue'
```


### `__init__`

```python
__init__(self, url: 'str | _CoreUrl | _BaseUrl') -> 'None'
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

The URL as a string, this will punycode encode the host if required.


### `build`

```python
build(*, scheme: 'str', username: 'str | None' = None, password: 'str | None' = None, host: 'str', port: 'int | None' = None, path: 'str | None' = None, query: 'str | None' = None, fragment: 'str | None' = None) -> 'Self'
```

Build a new `Url` instance from its component parts.

Args:
    scheme: The scheme part of the URL.
    username: The username part of the URL, or omit for no username.
    password: The password part of the URL, or omit for no password.
    host: The host part of the URL.
    port: The port part of the URL, or omit for no port.
    path: The path part of the URL, or omit for no path.
    query: The query part of the URL, or omit for no query.
    fragment: The fragment part of the URL, or omit for no fragment.

Returns:
    An instance of URL


### `encoded_string`

```python
encoded_string(self) -> 'str'
```

The URL's encoded string representation via __str__().

This returns the punycode-encoded host version of the URL as a string.


### `query_params`

```python
query_params(self) -> 'list[tuple[str, str]]'
```

The query part of the URL as a list of key-value pairs.

e.g. `[('foo', 'bar')]` in `https://user:pass@host:port/path?foo=bar#fragment`


### `serialize_url`

```python
serialize_url(url: 'Any', info: 'core_schema.SerializationInfo') -> 'str | Self'
```


### `unicode_host`

```python
unicode_host(self) -> 'str | None'
```

The host part of the URL as a unicode string, or `None`.

e.g. `host` in `https://user:pass@host:port/path?query#fragment`

If the URL must be punycode encoded, this is the decoded host, e.g if the input URL is `https://£££.com`,
`unicode_host()` will be `£££.com`


### `unicode_string`

```python
unicode_string(self) -> 'str'
```

The URL as a unicode string, unlike `__str__()` this will not punycode encode the host.

If the URL must be punycode encoded, this is the decoded string, e.g if the input URL is `https://£££.com`,
`unicode_string()` will be `https://£££.com`


## Properties

### `fragment`

The fragment part of the URL, or `None`.

e.g. `fragment` in `https://user:pass@host:port/path?query#fragment`


### `host`

The host part of the URL, or `None`.

If the URL must be punycode encoded, this is the encoded host, e.g if the input URL is `https://£££.com`,
`host` will be `xn--9aaa.com`


### `password`

The password part of the URL, or `None`.

e.g. `pass` in `https://user:pass@host:port/path?query#fragment`


### `path`

The path part of the URL, or `None`.

e.g. `/path` in `https://user:pass@host:port/path?query#fragment`


### `port`

The port part of the URL, or `None`.

e.g. `port` in `https://user:pass@host:port/path?query#fragment`


### `query`

The query part of the URL, or `None`.

e.g. `query` in `https://user:pass@host:port/path?query#fragment`


### `scheme`

The scheme part of the URL.

e.g. `https` in `https://user:pass@host:port/path?query#fragment`


### `username`

The username part of the URL, or `None`.

e.g. `user` in `https://user:pass@host:port/path?query#fragment`

