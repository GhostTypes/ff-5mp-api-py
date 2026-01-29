# NatsDsn

**Module:** `pydantic.networks`

A type that will accept any NATS DSN.

NATS is a connective technology built for the ever increasingly hyper-connected world.
It is a single technology that enables applications to securely communicate across
any combination of cloud vendors, on-premise, edge, web and mobile, and devices.
More: https://nats.io

## Signature

```python
NatsDsn(url: 'str | _CoreMultiHostUrl | _BaseMultiHostUrl') -> 'None'
```

## Methods

### `__deepcopy__`

```python
__deepcopy__(self, memo: 'dict') -> 'Self'
```


### `__get_pydantic_core_schema__`

```python
__get_pydantic_core_schema__(source: 'type[_BaseMultiHostUrl]', handler: 'GetCoreSchemaHandler') -> 'core_schema.CoreSchema'
```


### `__get_pydantic_json_schema__`

```python
__get_pydantic_json_schema__(core_schema: 'core_schema.CoreSchema', handler: '_schema_generation_shared.GetJsonSchemaHandler') -> 'JsonSchemaValue'
```


### `__init__`

```python
__init__(self, url: 'str | _CoreMultiHostUrl | _BaseMultiHostUrl') -> 'None'
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
build(*, scheme: 'str', hosts: 'list[MultiHostHost] | None' = None, username: 'str | None' = None, password: 'str | None' = None, host: 'str | None' = None, port: 'int | None' = None, path: 'str | None' = None, query: 'str | None' = None, fragment: 'str | None' = None) -> 'Self'
```

Build a new `MultiHostUrl` instance from its component parts.

This method takes either `hosts` - a list of `MultiHostHost` typed dicts, or the individual components
`username`, `password`, `host` and `port`.

Args:
    scheme: The scheme part of the URL.
    hosts: Multiple hosts to build the URL from.
    username: The username part of the URL.
    password: The password part of the URL.
    host: The host part of the URL.
    port: The port part of the URL.
    path: The path part of the URL.
    query: The query part of the URL, or omit for no query.
    fragment: The fragment part of the URL, or omit for no fragment.

Returns:
    An instance of `MultiHostUrl`


### `encoded_string`

```python
encoded_string(self) -> 'str'
```

The URL's encoded string representation via __str__().

This returns the punycode-encoded host version of the URL as a string.


### `hosts`

```python
hosts(self) -> 'list[MultiHostHost]'
```

The hosts of the `MultiHostUrl` as [`MultiHostHost`][pydantic_core.MultiHostHost] typed dicts.

```python
from pydantic_core import MultiHostUrl

mhu = MultiHostUrl('https://foo.com:123,foo:bar@bar.com/path')
print(mhu.hosts())
"""
[
    {'username': None, 'password': None, 'host': 'foo.com', 'port': 123},
    {'username': 'foo', 'password': 'bar', 'host': 'bar.com', 'port': 443}
]
```
Returns:
    A list of dicts, each representing a host.


### `query_params`

```python
query_params(self) -> 'list[tuple[str, str]]'
```

The query part of the URL as a list of key-value pairs.

e.g. `[('foo', 'bar')]` in `https://foo.com,bar.com/path?foo=bar#fragment`


### `serialize_url`

```python
serialize_url(url: 'Any', info: 'core_schema.SerializationInfo') -> 'str | Self'
```


### `unicode_string`

```python
unicode_string(self) -> 'str'
```

The URL as a unicode string, unlike `__str__()` this will not punycode encode the hosts.


## Properties

### `fragment`

The fragment part of the URL, or `None`.

e.g. `fragment` in `https://foo.com,bar.com/path?query#fragment`


### `path`

The path part of the URL, or `None`.

e.g. `/path` in `https://foo.com,bar.com/path?query#fragment`


### `query`

The query part of the URL, or `None`.

e.g. `query` in `https://foo.com,bar.com/path?query#fragment`


### `scheme`

The scheme part of the URL.

e.g. `https` in `https://foo.com,bar.com/path?query#fragment`

