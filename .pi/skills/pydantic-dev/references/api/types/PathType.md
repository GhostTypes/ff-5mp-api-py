# PathType

**Module:** `pydantic.types`

PathType(path_type: "Literal['file', 'dir', 'new', 'socket']")

## Signature

```python
PathType(path_type: "Literal['file', 'dir', 'new', 'socket']") -> None
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
__init__(self, path_type: "Literal['file', 'dir', 'new', 'socket']") -> None
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


### `validate_directory`

```python
validate_directory(path: 'Path', _: 'core_schema.ValidationInfo') -> 'Path'
```


### `validate_file`

```python
validate_file(path: 'Path', _: 'core_schema.ValidationInfo') -> 'Path'
```


### `validate_new`

```python
validate_new(path: 'Path', _: 'core_schema.ValidationInfo') -> 'Path'
```


### `validate_socket`

```python
validate_socket(path: 'Path', _: 'core_schema.ValidationInfo') -> 'Path'
```

