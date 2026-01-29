# HttpUrl

**Module:** `pydantic.networks`

A type that will accept any http or https URL.

* TLD not required
* Host not required
* Max length 2083

```python
from pydantic import BaseModel, HttpUrl, ValidationError

class MyModel(BaseModel):
    url: HttpUrl

m = MyModel(url='http://www.example.com')  # (1)!
print(m.url)
#> http://www.example.com/

try:
    MyModel(url='ftp://invalid.url')
except ValidationError as e:
    print(e)
    '''
    1 validation error for MyModel
    url
      URL scheme should be 'http' or 'https' [type=url_scheme, input_value='ftp://invalid.url', input_type=str]
    '''

try:
    MyModel(url='not a url')
except ValidationError as e:
    print(e)
    '''
    1 validation error for MyModel
    url
      Input should be a valid URL, relative URL without a base [type=url_parsing, input_value='not a url', input_type=str]
    '''
```

1. Note: mypy would prefer `m = MyModel(url=HttpUrl('http://www.example.com'))`, but Pydantic will convert the string to an HttpUrl instance anyway.

"International domains" (e.g. a URL where the host or TLD includes non-ascii characters) will be encoded via
[punycode](https://en.wikipedia.org/wiki/Punycode) (see
[this article](https://www.xudongz.com/blog/2017/idn-phishing/) for a good description of why this is important):

```python
from pydantic import BaseModel, HttpUrl

class MyModel(BaseModel):
    url: HttpUrl

m1 = MyModel(url='http://puny£code.com')
print(m1.url)
#> http://xn--punycode-eja.com/
m2 = MyModel(url='https://www.аррӏе.com/')
print(m2.url)
#> https://www.xn--80ak6aa92e.com/
m3 = MyModel(url='https://www.example.珠宝/')
print(m3.url)
#> https://www.example.xn--pbt977c/
```


!!! warning "Underscores in Hostnames"
    In Pydantic, underscores are allowed in all parts of a domain except the TLD.
    Technically this might be wrong - in theory the hostname cannot have underscores, but subdomains can.

    To explain this; consider the following two cases:

    - `exam_ple.co.uk`: the hostname is `exam_ple`, which should not be allowed since it contains an underscore.
    - `foo_bar.example.com` the hostname is `example`, which should be allowed since the underscore is in the subdomain.

    Without having an exhaustive list of TLDs, it would be impossible to differentiate between these two. Therefore
    underscores are allowed, but you can always do further validation in a validator if desired.

    Also, Chrome, Firefox, and Safari all currently accept `http://exam_ple.com` as a URL, so we're in good
    (or at least big) company.

## Signature

```python
HttpUrl(url: 'str | _CoreUrl | _BaseUrl') -> 'None'
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

