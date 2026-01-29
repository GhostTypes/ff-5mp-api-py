# FieldInfo

**Module:** `pydantic.fields`

This class holds information about a field.

`FieldInfo` is used for any field definition regardless of whether the [`Field()`][pydantic.fields.Field]
function is explicitly used.

!!! warning
    The `FieldInfo` class is meant to expose information about a field in a Pydantic model or dataclass.
    `FieldInfo` instances shouldn't be instantiated directly, nor mutated.

    If you need to derive a new model from another one and are willing to alter `FieldInfo` instances,
    refer to this [dynamic model example](../examples/dynamic_models.md).

Attributes:
    annotation: The type annotation of the field.
    default: The default value of the field.
    default_factory: A callable to generate the default value. The callable can either take 0 arguments
        (in which case it is called as is) or a single argument containing the already validated data.
    alias: The alias name of the field.
    alias_priority: The priority of the field's alias.
    validation_alias: The validation alias of the field.
    serialization_alias: The serialization alias of the field.
    title: The title of the field.
    field_title_generator: A callable that takes a field name and returns title for it.
    description: The description of the field.
    examples: List of examples of the field.
    exclude: Whether to exclude the field from the model serialization.
    exclude_if: A callable that determines whether to exclude a field during serialization based on its value.
    discriminator: Field name or Discriminator for discriminating the type in a tagged union.
    deprecated: A deprecation message, an instance of `warnings.deprecated` or the `typing_extensions.deprecated` backport,
        or a boolean. If `True`, a default deprecation message will be emitted when accessing the field.
    json_schema_extra: A dict or callable to provide extra JSON schema properties.
    frozen: Whether the field is frozen.
    validate_default: Whether to validate the default value of the field.
    repr: Whether to include the field in representation of the model.
    init: Whether the field should be included in the constructor of the dataclass.
    init_var: Whether the field should _only_ be included in the constructor of the dataclass, and not stored.
    kw_only: Whether the field should be a keyword-only argument in the constructor of the dataclass.
    metadata: The metadata list. Contains all the data that isn't expressed as direct `FieldInfo` attributes, including:

        * Type-specific constraints, such as `gt` or `min_length` (these are converted to metadata classes such as `annotated_types.Gt`).
        * Any other arbitrary object used within [`Annotated`][typing.Annotated] metadata
          (e.g. [custom types handlers](../concepts/types.md#as-an-annotation) or any object not recognized by Pydantic).

## Signature

```python
FieldInfo(**kwargs: 'Unpack[_FieldInfoInputs]') -> 'None'
```

## Methods

### `__init__`

```python
__init__(self, **kwargs: 'Unpack[_FieldInfoInputs]') -> 'None'
```

This class should generally not be initialized directly; instead, use the `pydantic.fields.Field` function
or one of the constructor classmethods.

See the signature of `pydantic.fields.Field` for more details about the expected arguments.


### `__pretty__`

```python
__pretty__(self, fmt: 'Callable[[Any], Any]', **kwargs: 'Any') -> 'Generator[Any]'
```

Used by devtools (https://python-devtools.helpmanual.io/) to pretty print objects.


### `__repr__`

```python
__repr__(self) -> 'str'
```

Return repr(self).


### `__repr_args__`

```python
__repr_args__(self) -> 'ReprArgs'
```

Returns the attributes to show in __str__, __repr__, and __pretty__ this is generally overridden.

Can either return:
* name - value pairs, e.g.: `[('foo_name', 'foo'), ('bar_name', ['b', 'a', 'r'])]`
* or, just values, e.g.: `[(None, 'foo'), (None, ['b', 'a', 'r'])]`


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


### `__str__`

```python
__str__(self) -> 'str'
```

Return str(self).


### `apply_typevars_map`

```python
apply_typevars_map(self, typevars_map: 'Mapping[TypeVar, Any] | None', globalns: 'GlobalsNamespace | None' = None, localns: 'MappingNamespace | None' = None) -> 'None'
```

Apply a `typevars_map` to the annotation.

This method is used when analyzing parametrized generic types to replace typevars with their concrete types.

This method applies the `typevars_map` to the annotation in place.

Args:
    typevars_map: A dictionary mapping type variables to their concrete types.
    globalns: The globals namespace to use during type annotation evaluation.
    localns: The locals namespace to use during type annotation evaluation.

See Also:
    pydantic._internal._generics.replace_types is used for replacing the typevars with
        their concrete types.


### `asdict`

```python
asdict(self) -> '_FieldInfoAsDict'
```

Return a dictionary representation of the `FieldInfo` instance.

The returned value is a dictionary with three items:

* `annotation`: The type annotation of the field.
* `metadata`: The metadata list.
* `attributes`: A mapping of the remaining `FieldInfo` attributes to their values (e.g. `alias`, `title`).


### `from_annotated_attribute`

```python
from_annotated_attribute(annotation: 'type[Any]', default: 'Any', *, _source: 'AnnotationSource' = <AnnotationSource.ANY: 7>) -> 'FieldInfo'
```

Create `FieldInfo` from an annotation with a default value.

This is used in cases like the following:

```python
from typing import Annotated

import annotated_types

import pydantic

class MyModel(pydantic.BaseModel):
    foo: int = 4  # <-- like this
    bar: Annotated[int, annotated_types.Gt(4)] = 4  # <-- or this
    spam: Annotated[int, pydantic.Field(gt=4)] = 4  # <-- or this
```

Args:
    annotation: The type annotation of the field.
    default: The default value of the field.

Returns:
    A field object with the passed values.


### `from_annotation`

```python
from_annotation(annotation: 'type[Any]', *, _source: 'AnnotationSource' = <AnnotationSource.ANY: 7>) -> 'FieldInfo'
```

Creates a `FieldInfo` instance from a bare annotation.

This function is used internally to create a `FieldInfo` from a bare annotation like this:

```python
import pydantic

class MyModel(pydantic.BaseModel):
    foo: int  # <-- like this
```

We also account for the case where the annotation can be an instance of `Annotated` and where
one of the (not first) arguments in `Annotated` is an instance of `FieldInfo`, e.g.:

```python
from typing import Annotated

import annotated_types

import pydantic

class MyModel(pydantic.BaseModel):
    foo: Annotated[int, annotated_types.Gt(42)]
    bar: Annotated[int, pydantic.Field(gt=42)]
```

Args:
    annotation: An annotation object.

Returns:
    An instance of the field metadata.


### `from_field`

```python
from_field(default: 'Any' = PydanticUndefined, **kwargs: 'Unpack[_FromFieldInfoInputs]') -> 'FieldInfo'
```

Create a new `FieldInfo` object with the `Field` function.

Args:
    default: The default value for the field. Defaults to Undefined.
    **kwargs: Additional arguments dictionary.

Raises:
    TypeError: If 'annotation' is passed as a keyword argument.

Returns:
    A new FieldInfo object with the given parameters.

Example:
    This is how you can create a field with default value like this:

    ```python
    import pydantic

    class MyModel(pydantic.BaseModel):
        foo: int = pydantic.Field(4)
    ```


### `get_default`

```python
get_default(self, *, call_default_factory: 'bool' = False, validated_data: 'dict[str, Any] | None' = None) -> 'Any'
```

Get the default value.

We expose an option for whether to call the default_factory (if present), as calling it may
result in side effects that we want to avoid. However, there are times when it really should
be called (namely, when instantiating a model via `model_construct`).

Args:
    call_default_factory: Whether to call the default factory or not.
    validated_data: The already validated data to be passed to the default factory.

Returns:
    The default value, calling the default factory if requested or `None` if not set.


### `is_required`

```python
is_required(self) -> 'bool'
```

Check if the field is required (i.e., does not have a default value or factory).

Returns:
    `True` if the field is required, `False` otherwise.


### `merge_field_infos`

```python
merge_field_infos(*field_infos: 'FieldInfo', **overrides: 'Any') -> 'FieldInfo'
```

Merge `FieldInfo` instances keeping only explicitly set attributes.

Later `FieldInfo` instances override earlier ones.

Returns:
    FieldInfo: A merged FieldInfo instance.


### `rebuild_annotation`

```python
rebuild_annotation(self) -> 'Any'
```

Attempts to rebuild the original annotation for use in function signatures.

If metadata is present, it adds it to the original annotation using
`Annotated`. Otherwise, it returns the original annotation as-is.

Note that because the metadata has been flattened, the original annotation
may not be reconstructed exactly as originally provided, e.g. if the original
type had unrecognized annotations, or was annotated with a call to `pydantic.Field`.

Returns:
    The rebuilt annotation.


## Properties

### `default_factory_takes_validated_data`

Whether the provided default factory callable has a validated data parameter.

Returns `None` if no default factory is set.


### `deprecation_message`

The deprecation message to be emitted, or `None` if not set.

