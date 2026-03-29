# model_json_schema

**Module:** `pydantic.json_schema`

## Signature

```python
model_json_schema(cls: 'type[BaseModel] | type[PydanticDataclass]', by_alias: 'bool' = True, ref_template: 'str' = '#/$defs/{model}', union_format: "Literal['any_of', 'primitive_type_array']" = 'any_of', schema_generator: 'type[GenerateJsonSchema]' = <class 'pydantic.json_schema.GenerateJsonSchema'>, mode: 'JsonSchemaMode' = 'validation') -> 'dict[str, Any]'
```

## Description

Utility function to generate a JSON Schema for a model.

Args:
    cls: The model class to generate a JSON Schema for.
    by_alias: If `True` (the default), fields will be serialized according to their alias.
        If `False`, fields will be serialized according to their attribute name.
    ref_template: The template to use for generating JSON Schema references.
    union_format: The format to use when combining schemas from unions together. Can be one of:

        - `'any_of'`: Use the [`anyOf`](https://json-schema.org/understanding-json-schema/reference/combining#anyOf)
          keyword to combine schemas (the default).
        - `'primitive_type_array'`: Use the [`type`](https://json-schema.org/understanding-json-schema/reference/type)
          keyword as an array of strings, containing each type of the combination. If any of the schemas is not a primitive
          type (`string`, `boolean`, `null`, `integer` or `number`) or contains constraints/metadata, falls back to
          `any_of`.
    schema_generator: The class to use for generating the JSON Schema.
    mode: The mode to use for generating the JSON Schema. It can be one of the following:

        - 'validation': Generate a JSON Schema for validating data.
        - 'serialization': Generate a JSON Schema for serializing data.

Returns:
    The generated JSON Schema.
