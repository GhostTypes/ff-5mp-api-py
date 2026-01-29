# UuidVersion

**Module:** `pydantic.types`

A field metadata class to indicate a [UUID](https://docs.python.org/3/library/uuid.html) version.

Use this class as an annotation via [`Annotated`](https://docs.python.org/3/library/typing.html#typing.Annotated), as seen below.

Attributes:
    uuid_version: The version of the UUID. Must be one of 1, 3, 4, 5, 6, 7 or 8.

Example:
    ```python
    from typing import Annotated
    from uuid import UUID

    from pydantic.types import UuidVersion

    UUID1 = Annotated[UUID, UuidVersion(1)]
    ```

## Signature

```python
UuidVersion(uuid_version: 'Literal[1, 3, 4, 5, 6, 7, 8]') -> None
```

## Methods

### `__get_pydantic_core_schema__`

```python
__get_pydantic_core_schema__(self, source: 'Any', handler: 'GetCoreSchemaHandler') -> 'core_schema.CoreSchema'
```


### `__get_pydantic_json_schema__`

```python
__get_pydantic_json_schema__(self, core_schema: 'core_schema.CoreSchema', handler: 'GetJsonSchemaHandler') -> 'JsonSchemaValue'
```


### `__init__`

```python
__init__(self, uuid_version: 'Literal[1, 3, 4, 5, 6, 7, 8]') -> None
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

