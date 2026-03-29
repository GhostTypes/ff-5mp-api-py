# create_model

**Module:** `pydantic.main`

## Signature

```python
create_model(model_name: 'str', /, *, __config__: 'ConfigDict | None' = None, __doc__: 'str | None' = None, __base__: 'type[ModelT] | tuple[type[ModelT], ...] | None' = None, __module__: 'str | None' = None, __validators__: 'dict[str, Callable[..., Any]] | None' = None, __cls_kwargs__: 'dict[str, Any] | None' = None, __qualname__: 'str | None' = None, **field_definitions: 'Any | tuple[str, Any]') -> 'type[ModelT]'
```

## Description

!!! abstract "Usage Documentation"
    [Dynamic Model Creation](../concepts/models.md#dynamic-model-creation)

Dynamically creates and returns a new Pydantic model, in other words, `create_model` dynamically creates a
subclass of [`BaseModel`][pydantic.BaseModel].

!!! warning
    This function may execute arbitrary code contained in field annotations, if string references need to be evaluated.

    See [Security implications of introspecting annotations](https://docs.python.org/3/library/annotationlib.html#annotationlib-security) for more information.

Args:
    model_name: The name of the newly created model.
    __config__: The configuration of the new model.
    __doc__: The docstring of the new model.
    __base__: The base class or classes for the new model.
    __module__: The name of the module that the model belongs to;
        if `None`, the value is taken from `sys._getframe(1)`
    __validators__: A dictionary of methods that validate fields. The keys are the names of the validation methods to
        be added to the model, and the values are the validation methods themselves. You can read more about functional
        validators [here](https://docs.pydantic.dev/2.9/concepts/validators/#field-validators).
    __cls_kwargs__: A dictionary of keyword arguments for class creation, such as `metaclass`.
    __qualname__: The qualified name of the newly created model.
    **field_definitions: Field definitions of the new model. Either:

        - a single element, representing the type annotation of the field.
        - a two-tuple, the first element being the type and the second element the assigned value
          (either a default or the [`Field()`][pydantic.Field] function).

Returns:
    The new [model][pydantic.BaseModel].

Raises:
    PydanticUserError: If `__base__` and `__config__` are both passed.
