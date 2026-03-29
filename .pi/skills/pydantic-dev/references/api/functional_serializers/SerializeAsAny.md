# SerializeAsAny

**Module:** `pydantic.functional_serializers`

Annotation used to mark a type as having duck-typing serialization behavior.

See [usage documentation](../concepts/serialization.md#serializing-with-duck-typing) for more details.

## Signature

```python
SerializeAsAny() -> None
```

## Methods

### `__class_getitem__`

```python
__class_getitem__(item: 'Any') -> 'Any'
```


### `__get_pydantic_core_schema__`

```python
__get_pydantic_core_schema__(self, source_type: 'Any', handler: 'GetCoreSchemaHandler') -> 'core_schema.CoreSchema'
```


### `__init__`

```python
__init__(self) -> None
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

