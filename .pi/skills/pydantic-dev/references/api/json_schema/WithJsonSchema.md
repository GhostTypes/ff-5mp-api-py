# WithJsonSchema

**Module:** `pydantic.json_schema`

!!! abstract "Usage Documentation"
    [`WithJsonSchema` Annotation](../concepts/json_schema.md#withjsonschema-annotation)

Add this as an annotation on a field to override the (base) JSON schema that would be generated for that field.
This provides a way to set a JSON schema for types that would otherwise raise errors when producing a JSON schema,
such as Callable, or types that have an is-instance core schema, without needing to go so far as creating a
custom subclass of pydantic.json_schema.GenerateJsonSchema.
Note that any _modifications_ to the schema that would normally be made (such as setting the title for model fields)
will still be performed.

If `mode` is set this will only apply to that schema generation mode, allowing you
to set different json schemas for validation and serialization.

## Signature

```python
WithJsonSchema(json_schema: 'JsonSchemaValue | None', mode: "Literal['validation', 'serialization'] | None" = None) -> None
```

## Methods

### `__get_pydantic_json_schema__`

```python
__get_pydantic_json_schema__(self, core_schema: 'core_schema.CoreSchema', handler: 'GetJsonSchemaHandler') -> 'JsonSchemaValue'
```


### `__init__`

```python
__init__(self, json_schema: 'JsonSchemaValue | None', mode: "Literal['validation', 'serialization'] | None" = None) -> None
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

