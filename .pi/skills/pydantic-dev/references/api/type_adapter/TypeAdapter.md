# TypeAdapter

**Module:** `pydantic.type_adapter`

!!! abstract "Usage Documentation"
    [`TypeAdapter`](../concepts/type_adapter.md)

Type adapters provide a flexible way to perform validation and serialization based on a Python type.

A `TypeAdapter` instance exposes some of the functionality from `BaseModel` instance methods
for types that do not have such methods (such as dataclasses, primitive types, and more).

**Note:** `TypeAdapter` instances are not types, and cannot be used as type annotations for fields.

Args:
    type: The type associated with the `TypeAdapter`.
    config: Configuration for the `TypeAdapter`, should be a dictionary conforming to
        [`ConfigDict`][pydantic.config.ConfigDict].

        !!! note
            You cannot provide a configuration when instantiating a `TypeAdapter` if the type you're using
            has its own config that cannot be overridden (ex: `BaseModel`, `TypedDict`, and `dataclass`). A
            [`type-adapter-config-unused`](../errors/usage_errors.md#type-adapter-config-unused) error will
            be raised in this case.
    _parent_depth: Depth at which to search for the [parent frame][frame-objects]. This frame is used when
        resolving forward annotations during schema building, by looking for the globals and locals of this
        frame. Defaults to 2, which will result in the frame where the `TypeAdapter` was instantiated.

        !!! note
            This parameter is named with an underscore to suggest its private nature and discourage use.
            It may be deprecated in a minor version, so we only recommend using it if you're comfortable
            with potential change in behavior/support. It's default value is 2 because internally,
            the `TypeAdapter` class makes another call to fetch the frame.
    module: The module that passes to plugin if provided.

Attributes:
    core_schema: The core schema for the type.
    validator: The schema validator for the type.
    serializer: The schema serializer for the type.
    pydantic_complete: Whether the core schema for the type is successfully built.

??? tip "Compatibility with `mypy`"
    Depending on the type used, `mypy` might raise an error when instantiating a `TypeAdapter`. As a workaround, you can explicitly
    annotate your variable:

    ```py
    from typing import Union

    from pydantic import TypeAdapter

    ta: TypeAdapter[Union[str, int]] = TypeAdapter(Union[str, int])  # type: ignore[arg-type]
    ```

??? info "Namespace management nuances and implementation details"

    Here, we collect some notes on namespace management, and subtle differences from `BaseModel`:

    `BaseModel` uses its own `__module__` to find out where it was defined
    and then looks for symbols to resolve forward references in those globals.
    On the other hand, `TypeAdapter` can be initialized with arbitrary objects,
    which may not be types and thus do not have a `__module__` available.
    So instead we look at the globals in our parent stack frame.

    It is expected that the `ns_resolver` passed to this function will have the correct
    namespace for the type we're adapting. See the source code for `TypeAdapter.__init__`
    and `TypeAdapter.rebuild` for various ways to construct this namespace.

    This works for the case where this function is called in a module that
    has the target of forward references in its scope, but
    does not always work for more complex cases.

    For example, take the following:

    ```python {title="a.py"}
    IntList = list[int]
    OuterDict = dict[str, 'IntList']
    ```

    ```python {test="skip" title="b.py"}
    from a import OuterDict

    from pydantic import TypeAdapter

    IntList = int  # replaces the symbol the forward reference is looking for
    v = TypeAdapter(OuterDict)
    v({'x': 1})  # should fail but doesn't
    ```

    If `OuterDict` were a `BaseModel`, this would work because it would resolve
    the forward reference within the `a.py` namespace.
    But `TypeAdapter(OuterDict)` can't determine what module `OuterDict` came from.

    In other words, the assumption that _all_ forward references exist in the
    module we are being called from is not technically always true.
    Although most of the time it is and it works fine for recursive models and such,
    `BaseModel`'s behavior isn't perfect either and _can_ break in similar ways,
    so there is no right or wrong between the two.

    But at the very least this behavior is _subtly_ different from `BaseModel`'s.

## Signature

```python
TypeAdapter(type: 'Any', *, config: 'ConfigDict | None' = None, _parent_depth: 'int' = 2, module: 'str | None' = None) -> 'None'
```

## Methods

### `__init__`

```python
__init__(self, type: 'Any', *, config: 'ConfigDict | None' = None, _parent_depth: 'int' = 2, module: 'str | None' = None) -> 'None'
```

Initialize self.  See help(type(self)) for accurate signature.


### `__repr__`

```python
__repr__(self) -> 'str'
```

Return repr(self).


### `dump_json`

```python
dump_json(self, instance: 'T', /, *, indent: 'int | None' = None, ensure_ascii: 'bool' = False, include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, by_alias: 'bool | None' = None, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False, exclude_computed_fields: 'bool' = False, round_trip: 'bool' = False, warnings: "bool | Literal['none', 'warn', 'error']" = True, fallback: 'Callable[[Any], Any] | None' = None, serialize_as_any: 'bool' = False, context: 'Any | None' = None) -> 'bytes'
```

!!! abstract "Usage Documentation"
    [JSON Serialization](../concepts/json.md#json-serialization)

Serialize an instance of the adapted type to JSON.

Args:
    instance: The instance to be serialized.
    indent: Number of spaces for JSON indentation.
    ensure_ascii: If `True`, the output is guaranteed to have all incoming non-ASCII characters escaped.
        If `False` (the default), these characters will be output as-is.
    include: Fields to include.
    exclude: Fields to exclude.
    by_alias: Whether to use alias names for field names.
    exclude_unset: Whether to exclude unset fields.
    exclude_defaults: Whether to exclude fields with default values.
    exclude_none: Whether to exclude fields with a value of `None`.
    exclude_computed_fields: Whether to exclude computed fields.
        While this can be useful for round-tripping, it is usually recommended to use the dedicated
        `round_trip` parameter instead.
    round_trip: Whether to serialize and deserialize the instance to ensure round-tripping.
    warnings: How to handle serialization errors. False/"none" ignores them, True/"warn" logs errors,
        "error" raises a [`PydanticSerializationError`][pydantic_core.PydanticSerializationError].
    fallback: A function to call when an unknown value is encountered. If not provided,
        a [`PydanticSerializationError`][pydantic_core.PydanticSerializationError] error is raised.
    serialize_as_any: Whether to serialize fields with duck-typing serialization behavior.
    context: Additional context to pass to the serializer.

Returns:
    The JSON representation of the given instance as bytes.


### `dump_python`

```python
dump_python(self, instance: 'T', /, *, mode: "Literal['json', 'python']" = 'python', include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, by_alias: 'bool | None' = None, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False, exclude_computed_fields: 'bool' = False, round_trip: 'bool' = False, warnings: "bool | Literal['none', 'warn', 'error']" = True, fallback: 'Callable[[Any], Any] | None' = None, serialize_as_any: 'bool' = False, context: 'Any | None' = None) -> 'Any'
```

Dump an instance of the adapted type to a Python object.

Args:
    instance: The Python object to serialize.
    mode: The output format.
    include: Fields to include in the output.
    exclude: Fields to exclude from the output.
    by_alias: Whether to use alias names for field names.
    exclude_unset: Whether to exclude unset fields.
    exclude_defaults: Whether to exclude fields with default values.
    exclude_none: Whether to exclude fields with None values.
    exclude_computed_fields: Whether to exclude computed fields.
        While this can be useful for round-tripping, it is usually recommended to use the dedicated
        `round_trip` parameter instead.
    round_trip: Whether to output the serialized data in a way that is compatible with deserialization.
    warnings: How to handle serialization errors. False/"none" ignores them, True/"warn" logs errors,
        "error" raises a [`PydanticSerializationError`][pydantic_core.PydanticSerializationError].
    fallback: A function to call when an unknown value is encountered. If not provided,
        a [`PydanticSerializationError`][pydantic_core.PydanticSerializationError] error is raised.
    serialize_as_any: Whether to serialize fields with duck-typing serialization behavior.
    context: Additional context to pass to the serializer.

Returns:
    The serialized object.


### `get_default_value`

```python
get_default_value(self, *, strict: 'bool | None' = None, context: 'Any | None' = None) -> 'Some[T] | None'
```

Get the default value for the wrapped type.

Args:
    strict: Whether to strictly check types.
    context: Additional context to pass to the validator.

Returns:
    The default value wrapped in a `Some` if there is one or None if not.


### `json_schema`

```python
json_schema(self, *, by_alias: 'bool' = True, ref_template: 'str' = '#/$defs/{model}', union_format: "Literal['any_of', 'primitive_type_array']" = 'any_of', schema_generator: 'type[GenerateJsonSchema]' = <class 'pydantic.json_schema.GenerateJsonSchema'>, mode: 'JsonSchemaMode' = 'validation') -> 'dict[str, Any]'
```

Generate a JSON schema for the adapted type.

Args:
    by_alias: Whether to use alias names for field names.
    ref_template: The format string used for generating $ref strings.
    union_format: The format to use when combining schemas from unions together. Can be one of:

        - `'any_of'`: Use the [`anyOf`](https://json-schema.org/understanding-json-schema/reference/combining#anyOf)
        keyword to combine schemas (the default).
        - `'primitive_type_array'`: Use the [`type`](https://json-schema.org/understanding-json-schema/reference/type)
        keyword as an array of strings, containing each type of the combination. If any of the schemas is not a primitive
        type (`string`, `boolean`, `null`, `integer` or `number`) or contains constraints/metadata, falls back to
        `any_of`.
    schema_generator: To override the logic used to generate the JSON schema, as a subclass of
        `GenerateJsonSchema` with your desired modifications
    mode: The mode in which to generate the schema.
    schema_generator: The generator class used for creating the schema.
    mode: The mode to use for schema generation.

Returns:
    The JSON schema for the model as a dictionary.


### `json_schemas`

```python
json_schemas(inputs: 'Iterable[tuple[JsonSchemaKeyT, JsonSchemaMode, TypeAdapter[Any]]]', /, *, by_alias: 'bool' = True, title: 'str | None' = None, description: 'str | None' = None, ref_template: 'str' = '#/$defs/{model}', union_format: "Literal['any_of', 'primitive_type_array']" = 'any_of', schema_generator: 'type[GenerateJsonSchema]' = <class 'pydantic.json_schema.GenerateJsonSchema'>) -> 'tuple[dict[tuple[JsonSchemaKeyT, JsonSchemaMode], JsonSchemaValue], JsonSchemaValue]'
```

Generate a JSON schema including definitions from multiple type adapters.

Args:
    inputs: Inputs to schema generation. The first two items will form the keys of the (first)
        output mapping; the type adapters will provide the core schemas that get converted into
        definitions in the output JSON schema.
    by_alias: Whether to use alias names.
    title: The title for the schema.
    description: The description for the schema.
    ref_template: The format string used for generating $ref strings.
    union_format: The format to use when combining schemas from unions together. Can be one of:

        - `'any_of'`: Use the [`anyOf`](https://json-schema.org/understanding-json-schema/reference/combining#anyOf)
        keyword to combine schemas (the default).
        - `'primitive_type_array'`: Use the [`type`](https://json-schema.org/understanding-json-schema/reference/type)
        keyword as an array of strings, containing each type of the combination. If any of the schemas is not a primitive
        type (`string`, `boolean`, `null`, `integer` or `number`) or contains constraints/metadata, falls back to
        `any_of`.
    schema_generator: The generator class used for creating the schema.

Returns:
    A tuple where:

        - The first element is a dictionary whose keys are tuples of JSON schema key type and JSON mode, and
            whose values are the JSON schema corresponding to that pair of inputs. (These schemas may have
            JsonRef references to definitions that are defined in the second returned element.)
        - The second element is a JSON schema containing all definitions referenced in the first returned
            element, along with the optional title and description keys.


### `rebuild`

```python
rebuild(self, *, force: 'bool' = False, raise_errors: 'bool' = True, _parent_namespace_depth: 'int' = 2, _types_namespace: '_namespace_utils.MappingNamespace | None' = None) -> 'bool | None'
```

Try to rebuild the pydantic-core schema for the adapter's type.

This may be necessary when one of the annotations is a ForwardRef which could not be resolved during
the initial attempt to build the schema, and automatic rebuilding fails.

Args:
    force: Whether to force the rebuilding of the type adapter's schema, defaults to `False`.
    raise_errors: Whether to raise errors, defaults to `True`.
    _parent_namespace_depth: Depth at which to search for the [parent frame][frame-objects]. This
        frame is used when resolving forward annotations during schema rebuilding, by looking for
        the locals of this frame. Defaults to 2, which will result in the frame where the method
        was called.
    _types_namespace: An explicit types namespace to use, instead of using the local namespace
        from the parent frame. Defaults to `None`.

Returns:
    Returns `None` if the schema is already "complete" and rebuilding was not required.
    If rebuilding _was_ required, returns `True` if rebuilding was successful, otherwise `False`.


### `validate_json`

```python
validate_json(self, data: 'str | bytes | bytearray', /, *, strict: 'bool | None' = None, extra: 'ExtraValues | None' = None, context: 'Any | None' = None, experimental_allow_partial: "bool | Literal['off', 'on', 'trailing-strings']" = False, by_alias: 'bool | None' = None, by_name: 'bool | None' = None) -> 'T'
```

!!! abstract "Usage Documentation"
    [JSON Parsing](../concepts/json.md#json-parsing)

Validate a JSON string or bytes against the model.

Args:
    data: The JSON data to validate against the model.
    strict: Whether to strictly check types.
    extra: Whether to ignore, allow, or forbid extra data during model validation.
        See the [`extra` configuration value][pydantic.ConfigDict.extra] for details.
    context: Additional context to use during validation.
    experimental_allow_partial: **Experimental** whether to enable
        [partial validation](../concepts/experimental.md#partial-validation), e.g. to process streams.
        * False / 'off': Default behavior, no partial validation.
        * True / 'on': Enable partial validation.
        * 'trailing-strings': Enable partial validation and allow trailing strings in the input.
    by_alias: Whether to use the field's alias when validating against the provided input data.
    by_name: Whether to use the field's name when validating against the provided input data.

Returns:
    The validated object.


### `validate_python`

```python
validate_python(self, object: 'Any', /, *, strict: 'bool | None' = None, extra: 'ExtraValues | None' = None, from_attributes: 'bool | None' = None, context: 'Any | None' = None, experimental_allow_partial: "bool | Literal['off', 'on', 'trailing-strings']" = False, by_alias: 'bool | None' = None, by_name: 'bool | None' = None) -> 'T'
```

Validate a Python object against the model.

Args:
    object: The Python object to validate against the model.
    strict: Whether to strictly check types.
    extra: Whether to ignore, allow, or forbid extra data during model validation.
        See the [`extra` configuration value][pydantic.ConfigDict.extra] for details.
    from_attributes: Whether to extract data from object attributes.
    context: Additional context to pass to the validator.
    experimental_allow_partial: **Experimental** whether to enable
        [partial validation](../concepts/experimental.md#partial-validation), e.g. to process streams.
        * False / 'off': Default behavior, no partial validation.
        * True / 'on': Enable partial validation.
        * 'trailing-strings': Enable partial validation and allow trailing strings in the input.
    by_alias: Whether to use the field's alias when validating against the provided input data.
    by_name: Whether to use the field's name when validating against the provided input data.

!!! note
    When using `TypeAdapter` with a Pydantic `dataclass`, the use of the `from_attributes`
    argument is not supported.

Returns:
    The validated object.


### `validate_strings`

```python
validate_strings(self, obj: 'Any', /, *, strict: 'bool | None' = None, extra: 'ExtraValues | None' = None, context: 'Any | None' = None, experimental_allow_partial: "bool | Literal['off', 'on', 'trailing-strings']" = False, by_alias: 'bool | None' = None, by_name: 'bool | None' = None) -> 'T'
```

Validate object contains string data against the model.

Args:
    obj: The object contains string data to validate.
    strict: Whether to strictly check types.
    extra: Whether to ignore, allow, or forbid extra data during model validation.
        See the [`extra` configuration value][pydantic.ConfigDict.extra] for details.
    context: Additional context to use during validation.
    experimental_allow_partial: **Experimental** whether to enable
        [partial validation](../concepts/experimental.md#partial-validation), e.g. to process streams.
        * False / 'off': Default behavior, no partial validation.
        * True / 'on': Enable partial validation.
        * 'trailing-strings': Enable partial validation and allow trailing strings in the input.
    by_alias: Whether to use the field's alias when validating against the provided input data.
    by_name: Whether to use the field's name when validating against the provided input data.

Returns:
    The validated object.

