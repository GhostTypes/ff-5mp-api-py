# models_json_schema

**Module:** `pydantic.json_schema`

## Signature

```python
models_json_schema(models: 'Sequence[tuple[type[BaseModel] | type[PydanticDataclass], JsonSchemaMode]]', *, by_alias: 'bool' = True, title: 'str | None' = None, description: 'str | None' = None, ref_template: 'str' = '#/$defs/{model}', union_format: "Literal['any_of', 'primitive_type_array']" = 'any_of', schema_generator: 'type[GenerateJsonSchema]' = <class 'pydantic.json_schema.GenerateJsonSchema'>) -> 'tuple[dict[tuple[type[BaseModel] | type[PydanticDataclass], JsonSchemaMode], JsonSchemaValue], JsonSchemaValue]'
```

## Description

Utility function to generate a JSON Schema for multiple models.

Args:
    models: A sequence of tuples of the form (model, mode).
    by_alias: Whether field aliases should be used as keys in the generated JSON Schema.
    title: The title of the generated JSON Schema.
    description: The description of the generated JSON Schema.
    ref_template: The reference template to use for generating JSON Schema references.
    union_format: The format to use when combining schemas from unions together. Can be one of:

        - `'any_of'`: Use the [`anyOf`](https://json-schema.org/understanding-json-schema/reference/combining#anyOf)
          keyword to combine schemas (the default).
        - `'primitive_type_array'`: Use the [`type`](https://json-schema.org/understanding-json-schema/reference/type)
          keyword as an array of strings, containing each type of the combination. If any of the schemas is not a primitive
          type (`string`, `boolean`, `null`, `integer` or `number`) or contains constraints/metadata, falls back to
          `any_of`.
    schema_generator: The schema generator to use for generating the JSON Schema.

Returns:
    A tuple where:
        - The first element is a dictionary whose keys are tuples of JSON schema key type and JSON mode, and
            whose values are the JSON schema corresponding to that pair of inputs. (These schemas may have
            JsonRef references to definitions that are defined in the second returned element.)
        - The second element is a JSON schema containing all definitions referenced in the first returned
                element, along with the optional title and description keys.
