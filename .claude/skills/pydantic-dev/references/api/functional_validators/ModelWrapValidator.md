# ModelWrapValidator

**Module:** `pydantic.functional_validators`

A `@model_validator` decorated function signature. This is used when `mode='wrap'`.

## Signature

```python
ModelWrapValidator(*args, **kwargs)
```

## Methods

### `__call__`

```python
__call__(self, cls: 'type[_ModelType]', value: 'Any', handler: 'ModelWrapValidatorHandler[_ModelType]', info: 'core_schema.ValidationInfo', /) -> '_ModelType'
```

Call self as a function.


### `__init__`

```python
__init__(self, *args, **kwargs)
```

