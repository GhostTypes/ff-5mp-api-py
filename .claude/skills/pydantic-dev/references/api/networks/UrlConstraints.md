# UrlConstraints

**Module:** `pydantic.networks`

Url constraints.

Attributes:
    max_length: The maximum length of the url. Defaults to `None`.
    allowed_schemes: The allowed schemes. Defaults to `None`.
    host_required: Whether the host is required. Defaults to `None`.
    default_host: The default host. Defaults to `None`.
    default_port: The default port. Defaults to `None`.
    default_path: The default path. Defaults to `None`.
    preserve_empty_path: Whether to preserve empty URL paths. Defaults to `None`.

## Signature

```python
UrlConstraints(max_length: 'int | None' = None, allowed_schemes: 'list[str] | None' = None, host_required: 'bool | None' = None, default_host: 'str | None' = None, default_port: 'int | None' = None, default_path: 'str | None' = None, preserve_empty_path: 'bool | None' = None) -> None
```

## Methods

### `__get_pydantic_core_schema__`

```python
__get_pydantic_core_schema__(self, source: 'Any', handler: 'GetCoreSchemaHandler') -> 'core_schema.CoreSchema'
```


### `__init__`

```python
__init__(self, max_length: 'int | None' = None, allowed_schemes: 'list[str] | None' = None, host_required: 'bool | None' = None, default_host: 'str | None' = None, default_port: 'int | None' = None, default_path: 'str | None' = None, preserve_empty_path: 'bool | None' = None) -> None
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


## Properties

### `defined_constraints`

Fetch a key / value mapping of constraints to values that are not None. Used for core schema updates.

