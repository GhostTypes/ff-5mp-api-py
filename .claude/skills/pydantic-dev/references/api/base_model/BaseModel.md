# BaseModel

**Module:** `pydantic.main`

!!! abstract "Usage Documentation"
    [Models](../concepts/models.md)

A base class for creating Pydantic models.

Attributes:
    __class_vars__: The names of the class variables defined on the model.
    __private_attributes__: Metadata about the private attributes of the model.
    __signature__: The synthesized `__init__` [`Signature`][inspect.Signature] of the model.

    __pydantic_complete__: Whether model building is completed, or if there are still undefined fields.
    __pydantic_core_schema__: The core schema of the model.
    __pydantic_custom_init__: Whether the model has a custom `__init__` function.
    __pydantic_decorators__: Metadata containing the decorators defined on the model.
        This replaces `Model.__validators__` and `Model.__root_validators__` from Pydantic V1.
    __pydantic_generic_metadata__: Metadata for generic models; contains data used for a similar purpose to
        __args__, __origin__, __parameters__ in typing-module generics. May eventually be replaced by these.
    __pydantic_parent_namespace__: Parent namespace of the model, used for automatic rebuilding of models.
    __pydantic_post_init__: The name of the post-init method for the model, if defined.
    __pydantic_root_model__: Whether the model is a [`RootModel`][pydantic.root_model.RootModel].
    __pydantic_serializer__: The `pydantic-core` `SchemaSerializer` used to dump instances of the model.
    __pydantic_validator__: The `pydantic-core` `SchemaValidator` used to validate instances of the model.

    __pydantic_fields__: A dictionary of field names and their corresponding [`FieldInfo`][pydantic.fields.FieldInfo] objects.
    __pydantic_computed_fields__: A dictionary of computed field names and their corresponding [`ComputedFieldInfo`][pydantic.fields.ComputedFieldInfo] objects.

    __pydantic_extra__: A dictionary containing extra values, if [`extra`][pydantic.config.ConfigDict.extra]
        is set to `'allow'`.
    __pydantic_fields_set__: The names of fields explicitly set during instantiation.
    __pydantic_private__: Values of private attributes set on the model instance.

## Signature

```python
BaseModel(**data: 'Any') -> 'None'
```

## Methods

### `__class_getitem__`

```python
__class_getitem__(typevar_values: 'type[Any] | tuple[type[Any], ...]') -> 'type[BaseModel] | _forward_ref.PydanticRecursiveRef'
```


### `__copy__`

```python
__copy__(self) -> 'Self'
```

Returns a shallow copy of the model.


### `__deepcopy__`

```python
__deepcopy__(self, memo: 'dict[int, Any] | None' = None) -> 'Self'
```

Returns a deep copy of the model.


### `__get_pydantic_core_schema__`

```python
__get_pydantic_core_schema__(source: 'type[BaseModel]', handler: 'GetCoreSchemaHandler', /) -> 'CoreSchema'
```


### `__get_pydantic_json_schema__`

```python
__get_pydantic_json_schema__(core_schema: 'CoreSchema', handler: 'GetJsonSchemaHandler', /) -> 'JsonSchemaValue'
```

Hook into generating the model's JSON schema.

Args:
    core_schema: A `pydantic-core` CoreSchema.
        You can ignore this argument and call the handler with a new CoreSchema,
        wrap this CoreSchema (`{'type': 'nullable', 'schema': current_schema}`),
        or just call the handler with the original schema.
    handler: Call into Pydantic's internal JSON schema generation.
        This will raise a `pydantic.errors.PydanticInvalidForJsonSchema` if JSON schema
        generation fails.
        Since this gets called by `BaseModel.model_json_schema` you can override the
        `schema_generator` argument to that function to change JSON schema generation globally
        for a type.

Returns:
    A JSON schema, as a Python object.


### `__getattr__`

```python
__getattr__(self, item: 'str') -> 'Any'
```


### `__init__`

```python
__init__(self, /, **data: 'Any') -> 'None'
```

Create a new model by parsing and validating input data from keyword arguments.

Raises [`ValidationError`][pydantic_core.ValidationError] if the input data cannot be
validated to form a valid model.

`self` is explicitly positional-only to allow `self` as a field name.


### `__iter__`

```python
__iter__(self) -> 'TupleGenerator'
```

So `dict(model)` works.


### `__pretty__`

```python
__pretty__(self, fmt: 'Callable[[Any], Any]', **kwargs: 'Any') -> 'Generator[Any]'
```

Used by devtools (https://python-devtools.helpmanual.io/) to pretty print objects.


### `__pydantic_init_subclass__`

```python
__pydantic_init_subclass__(**kwargs: 'Any') -> 'None'
```

This is intended to behave just like `__init_subclass__`, but is called by `ModelMetaclass`
only after basic class initialization is complete. In particular, attributes like `model_fields` will
be present when this is called, but forward annotations are not guaranteed to be resolved yet,
meaning that creating an instance of the class may fail.

This is necessary because `__init_subclass__` will always be called by `type.__new__`,
and it would require a prohibitively large refactor to the `ModelMetaclass` to ensure that
`type.__new__` was called in such a manner that the class would already be sufficiently initialized.

This will receive the same `kwargs` that would be passed to the standard `__init_subclass__`, namely,
any kwargs passed to the class definition that aren't used internally by Pydantic.

Args:
    **kwargs: Any keyword arguments passed to the class definition that aren't used internally
        by Pydantic.

Note:
    You may want to override [`__pydantic_on_complete__()`][pydantic.main.BaseModel.__pydantic_on_complete__]
    instead, which is called once the class and its fields are fully initialized and ready for validation.


### `__pydantic_on_complete__`

```python
__pydantic_on_complete__() -> 'None'
```

This is called once the class and its fields are fully initialized and ready to be used.

This typically happens when the class is created (just before
[`__pydantic_init_subclass__()`][pydantic.main.BaseModel.__pydantic_init_subclass__] is called on the superclass),
except when forward annotations are used that could not immediately be resolved.
In that case, it will be called later, when the model is rebuilt automatically or explicitly using
[`model_rebuild()`][pydantic.main.BaseModel.model_rebuild].


### `__replace__`

```python
__replace__(self, **changes: 'Any') -> 'Self'
```


### `__repr__`

```python
__repr__(self) -> 'str'
```

Return repr(self).


### `__repr_args__`

```python
__repr_args__(self) -> '_repr.ReprArgs'
```


### `__repr_name__`

```python
__repr_name__(self) -> 'str'
```

Name of the instance's class, used in __repr__.


### `__repr_recursion__`

```python
__repr_recursion__(self, object: 'Any') -> 'str'
```

Returns the string representation of a recursive object.


### `__repr_str__`

```python
__repr_str__(self, join_str: 'str') -> 'str'
```


### `__rich_repr__`

```python
__rich_repr__(self) -> 'RichReprResult'
```

Used by Rich (https://rich.readthedocs.io/en/stable/pretty.html) to pretty print objects.


### `__setstate__`

```python
__setstate__(self, state: 'dict[Any, Any]') -> 'None'
```


### `__str__`

```python
__str__(self) -> 'str'
```

Return str(self).


### `construct`

```python
construct(_fields_set: 'set[str] | None' = None, **values: 'Any') -> 'Self'
```


### `copy`

```python
copy(self, *, include: 'AbstractSetIntStr | MappingIntStrAny | None' = None, exclude: 'AbstractSetIntStr | MappingIntStrAny | None' = None, update: 'Dict[str, Any] | None' = None, deep: 'bool' = False) -> 'Self'
```

Returns a copy of the model.

!!! warning "Deprecated"
    This method is now deprecated; use `model_copy` instead.

If you need `include` or `exclude`, use:

```python {test="skip" lint="skip"}
data = self.model_dump(include=include, exclude=exclude, round_trip=True)
data = {**data, **(update or {})}
copied = self.model_validate(data)
```

Args:
    include: Optional set or mapping specifying which fields to include in the copied model.
    exclude: Optional set or mapping specifying which fields to exclude in the copied model.
    update: Optional dictionary of field-value pairs to override field values in the copied model.
    deep: If True, the values of fields that are Pydantic models will be deep-copied.

Returns:
    A copy of the model with included, excluded and updated fields as specified.


### `dict`

```python
dict(self, *, include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, by_alias: 'bool' = False, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False) -> 'Dict[str, Any]'
```


### `from_orm`

```python
from_orm(obj: 'Any') -> 'Self'
```


### `json`

```python
json(self, *, include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, by_alias: 'bool' = False, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False, encoder: 'Callable[[Any], Any] | None' = PydanticUndefined, models_as_dict: 'bool' = PydanticUndefined, **dumps_kwargs: 'Any') -> 'str'
```


### `model_construct`

```python
model_construct(_fields_set: 'set[str] | None' = None, **values: 'Any') -> 'Self'
```

Creates a new instance of the `Model` class with validated data.

Creates a new model setting `__dict__` and `__pydantic_fields_set__` from trusted or pre-validated data.
Default values are respected, but no other validation is performed.

!!! note
    `model_construct()` generally respects the `model_config.extra` setting on the provided model.
    That is, if `model_config.extra == 'allow'`, then all extra passed values are added to the model instance's `__dict__`
    and `__pydantic_extra__` fields. If `model_config.extra == 'ignore'` (the default), then all extra passed values are ignored.
    Because no validation is performed with a call to `model_construct()`, having `model_config.extra == 'forbid'` does not result in
    an error if extra values are passed, but they will be ignored.

Args:
    _fields_set: A set of field names that were originally explicitly set during instantiation. If provided,
        this is directly used for the [`model_fields_set`][pydantic.BaseModel.model_fields_set] attribute.
        Otherwise, the field names from the `values` argument will be used.
    values: Trusted or pre-validated data dictionary.

Returns:
    A new instance of the `Model` class with validated data.


### `model_copy`

```python
model_copy(self, *, update: 'Mapping[str, Any] | None' = None, deep: 'bool' = False) -> 'Self'
```

!!! abstract "Usage Documentation"
    [`model_copy`](../concepts/models.md#model-copy)

Returns a copy of the model.

!!! note
    The underlying instance's [`__dict__`][object.__dict__] attribute is copied. This
    might have unexpected side effects if you store anything in it, on top of the model
    fields (e.g. the value of [cached properties][functools.cached_property]).

Args:
    update: Values to change/add in the new model. Note: the data is not validated
        before creating the new model. You should trust this data.
    deep: Set to `True` to make a deep copy of the model.

Returns:
    New model instance.


### `model_dump`

```python
model_dump(self, *, mode: "Literal['json', 'python'] | str" = 'python', include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False, exclude_computed_fields: 'bool' = False, round_trip: 'bool' = False, warnings: "bool | Literal['none', 'warn', 'error']" = True, fallback: 'Callable[[Any], Any] | None' = None, serialize_as_any: 'bool' = False) -> 'dict[str, Any]'
```

!!! abstract "Usage Documentation"
    [`model_dump`](../concepts/serialization.md#python-mode)

Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.

Args:
    mode: The mode in which `to_python` should run.
        If mode is 'json', the output will only contain JSON serializable types.
        If mode is 'python', the output may contain non-JSON-serializable Python objects.
    include: A set of fields to include in the output.
    exclude: A set of fields to exclude from the output.
    context: Additional context to pass to the serializer.
    by_alias: Whether to use the field's alias in the dictionary key if defined.
    exclude_unset: Whether to exclude fields that have not been explicitly set.
    exclude_defaults: Whether to exclude fields that are set to their default value.
    exclude_none: Whether to exclude fields that have a value of `None`.
    exclude_computed_fields: Whether to exclude computed fields.
        While this can be useful for round-tripping, it is usually recommended to use the dedicated
        `round_trip` parameter instead.
    round_trip: If True, dumped values should be valid as input for non-idempotent types such as Json[T].
    warnings: How to handle serialization errors. False/"none" ignores them, True/"warn" logs errors,
        "error" raises a [`PydanticSerializationError`][pydantic_core.PydanticSerializationError].
    fallback: A function to call when an unknown value is encountered. If not provided,
        a [`PydanticSerializationError`][pydantic_core.PydanticSerializationError] error is raised.
    serialize_as_any: Whether to serialize fields with duck-typing serialization behavior.

Returns:
    A dictionary representation of the model.


### `model_dump_json`

```python
model_dump_json(self, *, indent: 'int | None' = None, ensure_ascii: 'bool' = False, include: 'IncEx | None' = None, exclude: 'IncEx | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, exclude_unset: 'bool' = False, exclude_defaults: 'bool' = False, exclude_none: 'bool' = False, exclude_computed_fields: 'bool' = False, round_trip: 'bool' = False, warnings: "bool | Literal['none', 'warn', 'error']" = True, fallback: 'Callable[[Any], Any] | None' = None, serialize_as_any: 'bool' = False) -> 'str'
```

!!! abstract "Usage Documentation"
    [`model_dump_json`](../concepts/serialization.md#json-mode)

Generates a JSON representation of the model using Pydantic's `to_json` method.

Args:
    indent: Indentation to use in the JSON output. If None is passed, the output will be compact.
    ensure_ascii: If `True`, the output is guaranteed to have all incoming non-ASCII characters escaped.
        If `False` (the default), these characters will be output as-is.
    include: Field(s) to include in the JSON output.
    exclude: Field(s) to exclude from the JSON output.
    context: Additional context to pass to the serializer.
    by_alias: Whether to serialize using field aliases.
    exclude_unset: Whether to exclude fields that have not been explicitly set.
    exclude_defaults: Whether to exclude fields that are set to their default value.
    exclude_none: Whether to exclude fields that have a value of `None`.
    exclude_computed_fields: Whether to exclude computed fields.
        While this can be useful for round-tripping, it is usually recommended to use the dedicated
        `round_trip` parameter instead.
    round_trip: If True, dumped values should be valid as input for non-idempotent types such as Json[T].
    warnings: How to handle serialization errors. False/"none" ignores them, True/"warn" logs errors,
        "error" raises a [`PydanticSerializationError`][pydantic_core.PydanticSerializationError].
    fallback: A function to call when an unknown value is encountered. If not provided,
        a [`PydanticSerializationError`][pydantic_core.PydanticSerializationError] error is raised.
    serialize_as_any: Whether to serialize fields with duck-typing serialization behavior.

Returns:
    A JSON string representation of the model.


### `model_json_schema`

```python
model_json_schema(by_alias: 'bool' = True, ref_template: 'str' = '#/$defs/{model}', schema_generator: 'type[GenerateJsonSchema]' = <class 'pydantic.json_schema.GenerateJsonSchema'>, mode: 'JsonSchemaMode' = 'validation', *, union_format: "Literal['any_of', 'primitive_type_array']" = 'any_of') -> 'dict[str, Any]'
```

Generates a JSON schema for a model class.

Args:
    by_alias: Whether to use attribute aliases or not.
    ref_template: The reference template.
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

Returns:
    The JSON schema for the given model class.


### `model_parametrized_name`

```python
model_parametrized_name(params: 'tuple[type[Any], ...]') -> 'str'
```

Compute the class name for parametrizations of generic classes.

This method can be overridden to achieve a custom naming scheme for generic BaseModels.

Args:
    params: Tuple of types of the class. Given a generic class
        `Model` with 2 type variables and a concrete model `Model[str, int]`,
        the value `(str, int)` would be passed to `params`.

Returns:
    String representing the new class where `params` are passed to `cls` as type variables.

Raises:
    TypeError: Raised when trying to generate concrete names for non-generic models.


### `model_post_init`

```python
model_post_init(self, context: 'Any', /) -> 'None'
```

Override this method to perform additional initialization after `__init__` and `model_construct`.
This is useful if you want to do some validation that requires the entire model to be initialized.


### `model_rebuild`

```python
model_rebuild(*, force: 'bool' = False, raise_errors: 'bool' = True, _parent_namespace_depth: 'int' = 2, _types_namespace: 'MappingNamespace | None' = None) -> 'bool | None'
```

Try to rebuild the pydantic-core schema for the model.

This may be necessary when one of the annotations is a ForwardRef which could not be resolved during
the initial attempt to build the schema, and automatic rebuilding fails.

Args:
    force: Whether to force the rebuilding of the model schema, defaults to `False`.
    raise_errors: Whether to raise errors, defaults to `True`.
    _parent_namespace_depth: The depth level of the parent namespace, defaults to 2.
    _types_namespace: The types namespace, defaults to `None`.

Returns:
    Returns `None` if the schema is already "complete" and rebuilding was not required.
    If rebuilding _was_ required, returns `True` if rebuilding was successful, otherwise `False`.


### `model_validate`

```python
model_validate(obj: 'Any', *, strict: 'bool | None' = None, extra: 'ExtraValues | None' = None, from_attributes: 'bool | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, by_name: 'bool | None' = None) -> 'Self'
```

Validate a pydantic model instance.

Args:
    obj: The object to validate.
    strict: Whether to enforce types strictly.
    extra: Whether to ignore, allow, or forbid extra data during model validation.
        See the [`extra` configuration value][pydantic.ConfigDict.extra] for details.
    from_attributes: Whether to extract data from object attributes.
    context: Additional context to pass to the validator.
    by_alias: Whether to use the field's alias when validating against the provided input data.
    by_name: Whether to use the field's name when validating against the provided input data.

Raises:
    ValidationError: If the object could not be validated.

Returns:
    The validated model instance.


### `model_validate_json`

```python
model_validate_json(json_data: 'str | bytes | bytearray', *, strict: 'bool | None' = None, extra: 'ExtraValues | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, by_name: 'bool | None' = None) -> 'Self'
```

!!! abstract "Usage Documentation"
    [JSON Parsing](../concepts/json.md#json-parsing)

Validate the given JSON data against the Pydantic model.

Args:
    json_data: The JSON data to validate.
    strict: Whether to enforce types strictly.
    extra: Whether to ignore, allow, or forbid extra data during model validation.
        See the [`extra` configuration value][pydantic.ConfigDict.extra] for details.
    context: Extra variables to pass to the validator.
    by_alias: Whether to use the field's alias when validating against the provided input data.
    by_name: Whether to use the field's name when validating against the provided input data.

Returns:
    The validated Pydantic model.

Raises:
    ValidationError: If `json_data` is not a JSON string or the object could not be validated.


### `model_validate_strings`

```python
model_validate_strings(obj: 'Any', *, strict: 'bool | None' = None, extra: 'ExtraValues | None' = None, context: 'Any | None' = None, by_alias: 'bool | None' = None, by_name: 'bool | None' = None) -> 'Self'
```

Validate the given object with string data against the Pydantic model.

Args:
    obj: The object containing string data to validate.
    strict: Whether to enforce types strictly.
    extra: Whether to ignore, allow, or forbid extra data during model validation.
        See the [`extra` configuration value][pydantic.ConfigDict.extra] for details.
    context: Extra variables to pass to the validator.
    by_alias: Whether to use the field's alias when validating against the provided input data.
    by_name: Whether to use the field's name when validating against the provided input data.

Returns:
    The validated Pydantic model.


### `parse_file`

```python
parse_file(path: 'str | Path', *, content_type: 'str | None' = None, encoding: 'str' = 'utf8', proto: 'DeprecatedParseProtocol | None' = None, allow_pickle: 'bool' = False) -> 'Self'
```


### `parse_obj`

```python
parse_obj(obj: 'Any') -> 'Self'
```


### `parse_raw`

```python
parse_raw(b: 'str | bytes', *, content_type: 'str | None' = None, encoding: 'str' = 'utf8', proto: 'DeprecatedParseProtocol | None' = None, allow_pickle: 'bool' = False) -> 'Self'
```


### `schema`

```python
schema(by_alias: 'bool' = True, ref_template: 'str' = '#/$defs/{model}') -> 'Dict[str, Any]'
```


### `schema_json`

```python
schema_json(*, by_alias: 'bool' = True, ref_template: 'str' = '#/$defs/{model}', **dumps_kwargs: 'Any') -> 'str'
```


### `update_forward_refs`

```python
update_forward_refs(**localns: 'Any') -> 'None'
```


### `validate`

```python
validate(value: 'Any') -> 'Self'
```


## Properties

### `__fields_set__`


### `model_extra`

Get extra fields set during validation.

Returns:
    A dictionary of extra fields, or `None` if `config.extra` is not set to `"allow"`.


### `model_fields_set`

Returns the set of fields that have been explicitly set on this model instance.

Returns:
    A set of strings representing the fields that have been set,
        i.e. that were not filled from defaults.

