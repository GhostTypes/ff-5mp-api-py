# Examples

**Module:** `pydantic.json_schema`

Add examples to a JSON schema.

If the JSON Schema already contains examples, the provided examples
will be appended.

If `mode` is set this will only apply to that schema generation mode,
allowing you to add different examples for validation and serialization.

## Signature

```python
Examples(examples: 'dict[str, Any] | list[Any]', mode: "Literal['validation', 'serialization'] | None" = None) -> 'None'
```

## Methods

### `__get_pydantic_json_schema__`

```python
__get_pydantic_json_schema__(self, core_schema: 'core_schema.CoreSchema', handler: 'GetJsonSchemaHandler') -> 'JsonSchemaValue'
```


### `__init__`

```python
__init__(self, examples: 'dict[str, Any] | list[Any]', mode: "Literal['validation', 'serialization'] | None" = None) -> 'None'
```

Initialize self.  See help(type(self)) for accurate signature.

