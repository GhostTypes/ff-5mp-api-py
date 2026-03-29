# GenerateJsonSchema

**Module:** `pydantic.json_schema`

!!! abstract "Usage Documentation"
    [Customizing the JSON Schema Generation Process](../concepts/json_schema.md#customizing-the-json-schema-generation-process)

A class for generating JSON schemas.

This class generates JSON schemas based on configured parameters. The default schema dialect
is [https://json-schema.org/draft/2020-12/schema](https://json-schema.org/draft/2020-12/schema).
The class uses `by_alias` to configure how fields with
multiple names are handled and `ref_template` to format reference names.

Attributes:
    schema_dialect: The JSON schema dialect used to generate the schema. See
        [Declaring a Dialect](https://json-schema.org/understanding-json-schema/reference/schema.html#id4)
        in the JSON Schema documentation for more information about dialects.
    ignored_warning_kinds: Warnings to ignore when generating the schema. `self.render_warning_message` will
        do nothing if its argument `kind` is in `ignored_warning_kinds`;
        this value can be modified on subclasses to easily control which warnings are emitted.
    by_alias: Whether to use field aliases when generating the schema.
    ref_template: The format string used when generating reference names.
    core_to_json_refs: A mapping of core refs to JSON refs.
    core_to_defs_refs: A mapping of core refs to definition refs.
    defs_to_core_refs: A mapping of definition refs to core refs.
    json_to_defs_refs: A mapping of JSON refs to definition refs.
    definitions: Definitions in the schema.

Args:
    by_alias: Whether to use field aliases in the generated schemas.
    ref_template: The format string to use when generating reference names.
    union_format: The format to use when combining schemas from unions together. Can be one of:

        - `'any_of'`: Use the [`anyOf`](https://json-schema.org/understanding-json-schema/reference/combining#anyOf)
          keyword to combine schemas (the default).
        - `'primitive_type_array'`: Use the [`type`](https://json-schema.org/understanding-json-schema/reference/type)
          keyword as an array of strings, containing each type of the combination. If any of the schemas is not a primitive
          type (`string`, `boolean`, `null`, `integer` or `number`) or contains constraints/metadata, falls back to
          `any_of`.

Raises:
    JsonSchemaError: If the instance of the class is inadvertently reused after generating a schema.

## Signature

```python
GenerateJsonSchema(by_alias: 'bool' = True, ref_template: 'str' = '#/$defs/{model}', union_format: "Literal['any_of', 'primitive_type_array']" = 'any_of') -> 'None'
```

## Methods

### `__init__`

```python
__init__(self, by_alias: 'bool' = True, ref_template: 'str' = '#/$defs/{model}', union_format: "Literal['any_of', 'primitive_type_array']" = 'any_of') -> 'None'
```

Initialize self.  See help(type(self)) for accurate signature.


### `any_schema`

```python
any_schema(self, schema: 'core_schema.AnySchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches any value.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `arguments_schema`

```python
arguments_schema(self, schema: 'core_schema.ArgumentsSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a schema that defines a function's arguments.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `arguments_v3_schema`

```python
arguments_v3_schema(self, schema: 'core_schema.ArgumentsV3Schema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a schema that defines a function's arguments.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `bool_schema`

```python
bool_schema(self, schema: 'core_schema.BoolSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a bool value.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `build_schema_type_to_method`

```python
build_schema_type_to_method(self) -> 'dict[CoreSchemaOrFieldType, Callable[[CoreSchemaOrField], JsonSchemaValue]]'
```

Builds a dictionary mapping fields to methods for generating JSON schemas.

Returns:
    A dictionary containing the mapping of `CoreSchemaOrFieldType` to a handler method.

Raises:
    TypeError: If no method has been defined for generating a JSON schema for a given pydantic core schema type.


### `bytes_schema`

```python
bytes_schema(self, schema: 'core_schema.BytesSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a bytes value.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `call_schema`

```python
call_schema(self, schema: 'core_schema.CallSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a schema that defines a function call.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `callable_schema`

```python
callable_schema(self, schema: 'core_schema.CallableSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a callable value.

Unless overridden in a subclass, this raises an error.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `chain_schema`

```python
chain_schema(self, schema: 'core_schema.ChainSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a core_schema.ChainSchema.

When generating a schema for validation, we return the validation JSON schema for the first step in the chain.
For serialization, we return the serialization JSON schema for the last step in the chain.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `complex_schema`

```python
complex_schema(self, schema: 'core_schema.ComplexSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a complex number.

JSON has no standard way to represent complex numbers. Complex number is not a numeric
type. Here we represent complex number as strings following the rule defined by Python.
For instance, '1+2j' is an accepted complex string. Details can be found in
[Python's `complex` documentation][complex].

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `computed_field_schema`

```python
computed_field_schema(self, schema: 'core_schema.ComputedField') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a schema that defines a computed field.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `custom_error_schema`

```python
custom_error_schema(self, schema: 'core_schema.CustomErrorSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a schema that defines a custom error.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `dataclass_args_schema`

```python
dataclass_args_schema(self, schema: 'core_schema.DataclassArgsSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a schema that defines a dataclass's constructor arguments.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `dataclass_field_schema`

```python
dataclass_field_schema(self, schema: 'core_schema.DataclassField') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a schema that defines a dataclass field.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `dataclass_schema`

```python
dataclass_schema(self, schema: 'core_schema.DataclassSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a schema that defines a dataclass.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `date_schema`

```python
date_schema(self, schema: 'core_schema.DateSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a date value.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `datetime_schema`

```python
datetime_schema(self, schema: 'core_schema.DatetimeSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a datetime value.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `decimal_schema`

```python
decimal_schema(self, schema: 'core_schema.DecimalSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a decimal value.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `default_schema`

```python
default_schema(self, schema: 'core_schema.WithDefaultSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a schema with a default value.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `definition_ref_schema`

```python
definition_ref_schema(self, schema: 'core_schema.DefinitionReferenceSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a schema that references a definition.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `definitions_schema`

```python
definitions_schema(self, schema: 'core_schema.DefinitionsSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a schema that defines a JSON object with definitions.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `dict_schema`

```python
dict_schema(self, schema: 'core_schema.DictSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a dict schema.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `emit_warning`

```python
emit_warning(self, kind: 'JsonSchemaWarningKind', detail: 'str') -> 'None'
```

This method simply emits PydanticJsonSchemaWarnings based on handling in the `warning_message` method.


### `encode_default`

```python
encode_default(self, dft: 'Any') -> 'Any'
```

Encode a default value to a JSON-serializable value.

This is used to encode default values for fields in the generated JSON schema.

Args:
    dft: The default value to encode.

Returns:
    The encoded default value.


### `enum_schema`

```python
enum_schema(self, schema: 'core_schema.EnumSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches an Enum value.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `field_is_present`

```python
field_is_present(self, field: 'CoreSchemaField') -> 'bool'
```

Whether the field should be included in the generated JSON schema.

Args:
    field: The schema for the field itself.

Returns:
    `True` if the field should be included in the generated JSON schema, `False` otherwise.


### `field_is_required`

```python
field_is_required(self, field: 'core_schema.ModelField | core_schema.DataclassField | core_schema.TypedDictField', total: 'bool') -> 'bool'
```

Whether the field should be marked as required in the generated JSON schema.
(Note that this is irrelevant if the field is not present in the JSON schema.).

Args:
    field: The schema for the field itself.
    total: Only applies to `TypedDictField`s.
        Indicates if the `TypedDict` this field belongs to is total, in which case any fields that don't
        explicitly specify `required=False` are required.

Returns:
    `True` if the field should be marked as required in the generated JSON schema, `False` otherwise.


### `field_title_should_be_set`

```python
field_title_should_be_set(self, schema: 'CoreSchemaOrField') -> 'bool'
```

Returns true if a field with the given schema should have a title set based on the field name.

Intuitively, we want this to return true for schemas that wouldn't otherwise provide their own title
(e.g., int, float, str), and false for those that would (e.g., BaseModel subclasses).

Args:
    schema: The schema to check.

Returns:
    `True` if the field should have a title set, `False` otherwise.


### `float_schema`

```python
float_schema(self, schema: 'core_schema.FloatSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a float value.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `frozenset_schema`

```python
frozenset_schema(self, schema: 'core_schema.FrozenSetSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a frozenset schema.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `function_after_schema`

```python
function_after_schema(self, schema: 'core_schema.AfterValidatorFunctionSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a function-after schema.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `function_before_schema`

```python
function_before_schema(self, schema: 'core_schema.BeforeValidatorFunctionSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a function-before schema.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `function_plain_schema`

```python
function_plain_schema(self, schema: 'core_schema.PlainValidatorFunctionSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a function-plain schema.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `function_wrap_schema`

```python
function_wrap_schema(self, schema: 'core_schema.WrapValidatorFunctionSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a function-wrap schema.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `generate`

```python
generate(self, schema: 'CoreSchema', mode: 'JsonSchemaMode' = 'validation') -> 'JsonSchemaValue'
```

Generates a JSON schema for a specified schema in a specified mode.

Args:
    schema: A Pydantic model.
    mode: The mode in which to generate the schema. Defaults to 'validation'.

Returns:
    A JSON schema representing the specified schema.

Raises:
    PydanticUserError: If the JSON schema generator has already been used to generate a JSON schema.


### `generate_definitions`

```python
generate_definitions(self, inputs: 'Sequence[tuple[JsonSchemaKeyT, JsonSchemaMode, core_schema.CoreSchema]]') -> 'tuple[dict[tuple[JsonSchemaKeyT, JsonSchemaMode], JsonSchemaValue], dict[DefsRef, JsonSchemaValue]]'
```

Generates JSON schema definitions from a list of core schemas, pairing the generated definitions with a
mapping that links the input keys to the definition references.

Args:
    inputs: A sequence of tuples, where:

        - The first element is a JSON schema key type.
        - The second element is the JSON mode: either 'validation' or 'serialization'.
        - The third element is a core schema.

Returns:
    A tuple where:

        - The first element is a dictionary whose keys are tuples of JSON schema key type and JSON mode, and
            whose values are the JSON schema corresponding to that pair of inputs. (These schemas may have
            JsonRef references to definitions that are defined in the second returned element.)
        - The second element is a dictionary whose keys are definition references for the JSON schemas
            from the first returned element, and whose values are the actual JSON schema definitions.

Raises:
    PydanticUserError: Raised if the JSON schema generator has already been used to generate a JSON schema.


### `generate_inner`

```python
generate_inner(self, schema: 'CoreSchemaOrField') -> 'JsonSchemaValue'
```

Generates a JSON schema for a given core schema.

Args:
    schema: The given core schema.

Returns:
    The generated JSON schema.

TODO: the nested function definitions here seem like bad practice, I'd like to unpack these
in a future PR. It'd be great if we could shorten the call stack a bit for JSON schema generation,
and I think there's potential for that here.


### `generator_schema`

```python
generator_schema(self, schema: 'core_schema.GeneratorSchema') -> 'JsonSchemaValue'
```

Returns a JSON schema that represents the provided GeneratorSchema.

Args:
    schema: The schema.

Returns:
    The generated JSON schema.


### `get_argument_name`

```python
get_argument_name(self, argument: 'core_schema.ArgumentsParameter | core_schema.ArgumentsV3Parameter') -> 'str'
```

Retrieves the name of an argument.

Args:
    argument: The core schema.

Returns:
    The name of the argument.


### `get_cache_defs_ref_schema`

```python
get_cache_defs_ref_schema(self, core_ref: 'CoreRef') -> 'tuple[DefsRef, JsonSchemaValue]'
```

This method wraps the get_defs_ref method with some cache-lookup/population logic,
and returns both the produced defs_ref and the JSON schema that will refer to the right definition.

Args:
    core_ref: The core reference to get the definitions reference for.

Returns:
    A tuple of the definitions reference and the JSON schema that will refer to it.


### `get_default_value`

```python
get_default_value(self, schema: 'core_schema.WithDefaultSchema') -> 'Any'
```

Get the default value to be used when generating a JSON Schema for a core schema with a default.

The default implementation is to use the statically defined default value. This method can be overridden
if you want to make use of the default factory.

Args:
    schema: The `'with-default'` core schema.

Returns:
    The default value to use, or [`NoDefault`][pydantic.json_schema.NoDefault] if no default
        value is available.


### `get_defs_ref`

```python
get_defs_ref(self, core_mode_ref: 'CoreModeRef') -> 'DefsRef'
```

Override this method to change the way that definitions keys are generated from a core reference.

Args:
    core_mode_ref: The core reference.

Returns:
    The definitions key.


### `get_flattened_anyof`

```python
get_flattened_anyof(self, schemas: 'list[JsonSchemaValue]') -> 'JsonSchemaValue'
```


### `get_json_ref_counts`

```python
get_json_ref_counts(self, json_schema: 'JsonSchemaValue') -> 'dict[JsonRef, int]'
```

Get all values corresponding to the key '$ref' anywhere in the json_schema.


### `get_schema_from_definitions`

```python
get_schema_from_definitions(self, json_ref: 'JsonRef') -> 'JsonSchemaValue | None'
```


### `get_title_from_name`

```python
get_title_from_name(self, name: 'str') -> 'str'
```

Retrieves a title from a name.

Args:
    name: The name to retrieve a title from.

Returns:
    The title.


### `get_union_of_schemas`

```python
get_union_of_schemas(self, schemas: 'list[JsonSchemaValue]') -> 'JsonSchemaValue'
```

Returns the JSON Schema representation for the union of the provided JSON Schemas.

The result depends on the configured `'union_format'`.

Args:
    schemas: The list of JSON Schemas to be included in the union.

Returns:
    The JSON Schema representing the union of schemas.


### `handle_invalid_for_json_schema`

```python
handle_invalid_for_json_schema(self, schema: 'CoreSchemaOrField', error_info: 'str') -> 'JsonSchemaValue'
```


### `handle_ref_overrides`

```python
handle_ref_overrides(self, json_schema: 'JsonSchemaValue') -> 'JsonSchemaValue'
```

Remove any sibling keys that are redundant with the referenced schema.

Args:
    json_schema: The schema to remove redundant sibling keys from.

Returns:
    The schema with redundant sibling keys removed.


### `int_schema`

```python
int_schema(self, schema: 'core_schema.IntSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches an int value.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `invalid_schema`

```python
invalid_schema(self, schema: 'core_schema.InvalidSchema') -> 'JsonSchemaValue'
```

Placeholder - should never be called.


### `is_instance_schema`

```python
is_instance_schema(self, schema: 'core_schema.IsInstanceSchema') -> 'JsonSchemaValue'
```

Handles JSON schema generation for a core schema that checks if a value is an instance of a class.

Unless overridden in a subclass, this raises an error.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `is_subclass_schema`

```python
is_subclass_schema(self, schema: 'core_schema.IsSubclassSchema') -> 'JsonSchemaValue'
```

Handles JSON schema generation for a core schema that checks if a value is a subclass of a class.

For backwards compatibility with v1, this does not raise an error, but can be overridden to change this.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `json_or_python_schema`

```python
json_or_python_schema(self, schema: 'core_schema.JsonOrPythonSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a schema that allows values matching either the JSON schema or the
Python schema.

The JSON schema is used instead of the Python schema. If you want to use the Python schema, you should override
this method.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `json_schema`

```python
json_schema(self, schema: 'core_schema.JsonSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a schema that defines a JSON object.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `kw_arguments_schema`

```python
kw_arguments_schema(self, arguments: 'list[core_schema.ArgumentsParameter]', var_kwargs_schema: 'CoreSchema | None') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a schema that defines a function's keyword arguments.

Args:
    arguments: The core schema.

Returns:
    The generated JSON schema.


### `lax_or_strict_schema`

```python
lax_or_strict_schema(self, schema: 'core_schema.LaxOrStrictSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a schema that allows values matching either the lax schema or the
strict schema.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `list_schema`

```python
list_schema(self, schema: 'core_schema.ListSchema') -> 'JsonSchemaValue'
```

Returns a schema that matches a list schema.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `literal_schema`

```python
literal_schema(self, schema: 'core_schema.LiteralSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a literal value.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `missing_sentinel_schema`

```python
missing_sentinel_schema(self, schema: 'core_schema.MissingSentinelSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches the `MISSING` sentinel value.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `model_field_schema`

```python
model_field_schema(self, schema: 'core_schema.ModelField') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a schema that defines a model field.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `model_fields_schema`

```python
model_fields_schema(self, schema: 'core_schema.ModelFieldsSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a schema that defines a model's fields.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `model_schema`

```python
model_schema(self, schema: 'core_schema.ModelSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a schema that defines a model.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `multi_host_url_schema`

```python
multi_host_url_schema(self, schema: 'core_schema.MultiHostUrlSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a schema that defines a URL that can be used with multiple hosts.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `none_schema`

```python
none_schema(self, schema: 'core_schema.NoneSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches `None`.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `normalize_name`

```python
normalize_name(self, name: 'str') -> 'str'
```

Normalizes a name to be used as a key in a dictionary.

Args:
    name: The name to normalize.

Returns:
    The normalized name.


### `nullable_schema`

```python
nullable_schema(self, schema: 'core_schema.NullableSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a schema that allows null values.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `p_arguments_schema`

```python
p_arguments_schema(self, arguments: 'list[core_schema.ArgumentsParameter]', var_args_schema: 'CoreSchema | None') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a schema that defines a function's positional arguments.

Args:
    arguments: The core schema.

Returns:
    The generated JSON schema.


### `render_warning_message`

```python
render_warning_message(self, kind: 'JsonSchemaWarningKind', detail: 'str') -> 'str | None'
```

This method is responsible for ignoring warnings as desired, and for formatting the warning messages.

You can override the value of `ignored_warning_kinds` in a subclass of GenerateJsonSchema
to modify what warnings are generated. If you want more control, you can override this method;
just return None in situations where you don't want warnings to be emitted.

Args:
    kind: The kind of warning to render. It can be one of the following:

        - 'skipped-choice': A choice field was skipped because it had no valid choices.
        - 'non-serializable-default': A default value was skipped because it was not JSON-serializable.
    detail: A string with additional details about the warning.

Returns:
    The formatted warning message, or `None` if no warning should be emitted.


### `resolve_ref_schema`

```python
resolve_ref_schema(self, json_schema: 'JsonSchemaValue') -> 'JsonSchemaValue'
```

Resolve a JsonSchemaValue to the non-ref schema if it is a $ref schema.

Args:
    json_schema: The schema to resolve.

Returns:
    The resolved schema.

Raises:
    RuntimeError: If the schema reference can't be found in definitions.


### `ser_schema`

```python
ser_schema(self, schema: 'core_schema.SerSchema | core_schema.IncExSeqSerSchema | core_schema.IncExDictSerSchema') -> 'JsonSchemaValue | None'
```

Generates a JSON schema that matches a schema that defines a serialized object.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `set_schema`

```python
set_schema(self, schema: 'core_schema.SetSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a set schema.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `sort`

```python
sort(self, value: 'JsonSchemaValue', parent_key: 'str | None' = None) -> 'JsonSchemaValue'
```

Override this method to customize the sorting of the JSON schema (e.g., don't sort at all, sort all keys unconditionally, etc.)

By default, alphabetically sort the keys in the JSON schema, skipping the 'properties' and 'default' keys to preserve field definition order.
This sort is recursive, so it will sort all nested dictionaries as well.


### `str_schema`

```python
str_schema(self, schema: 'core_schema.StringSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a string value.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `tagged_union_schema`

```python
tagged_union_schema(self, schema: 'core_schema.TaggedUnionSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a schema that allows values matching any of the given schemas, where
the schemas are tagged with a discriminator field that indicates which schema should be used to validate
the value.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `time_schema`

```python
time_schema(self, schema: 'core_schema.TimeSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a time value.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `timedelta_schema`

```python
timedelta_schema(self, schema: 'core_schema.TimedeltaSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a timedelta value.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `tuple_positional_schema`

```python
tuple_positional_schema(self, schema: 'core_schema.TupleSchema') -> 'JsonSchemaValue'
```

Replaced by `tuple_schema`.


### `tuple_schema`

```python
tuple_schema(self, schema: 'core_schema.TupleSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a tuple schema e.g. `tuple[int,
str, bool]` or `tuple[int, ...]`.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `tuple_variable_schema`

```python
tuple_variable_schema(self, schema: 'core_schema.TupleSchema') -> 'JsonSchemaValue'
```

Replaced by `tuple_schema`.


### `typed_dict_field_schema`

```python
typed_dict_field_schema(self, schema: 'core_schema.TypedDictField') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a schema that defines a typed dict field.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `typed_dict_schema`

```python
typed_dict_schema(self, schema: 'core_schema.TypedDictSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a schema that defines a typed dict.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `union_schema`

```python
union_schema(self, schema: 'core_schema.UnionSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a schema that allows values matching any of the given schemas.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `update_with_validations`

```python
update_with_validations(self, json_schema: 'JsonSchemaValue', core_schema: 'CoreSchema', mapping: 'dict[str, str]') -> 'None'
```

Update the json_schema with the corresponding validations specified in the core_schema,
using the provided mapping to translate keys in core_schema to the appropriate keys for a JSON schema.

Args:
    json_schema: The JSON schema to update.
    core_schema: The core schema to get the validations from.
    mapping: A mapping from core_schema attribute names to the corresponding JSON schema attribute names.


### `url_schema`

```python
url_schema(self, schema: 'core_schema.UrlSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a schema that defines a URL.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


### `uuid_schema`

```python
uuid_schema(self, schema: 'core_schema.UuidSchema') -> 'JsonSchemaValue'
```

Generates a JSON schema that matches a UUID.

Args:
    schema: The core schema.

Returns:
    The generated JSON schema.


## Properties

### `mode`

