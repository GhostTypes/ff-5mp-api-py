# ModelWrapValidatorWithoutInfo

**Module:** `pydantic.functional_validators`

A `@model_validator` decorated function signature.
This is used when `mode='wrap'` and the function does not have info argument.

## Signature

```python
ModelWrapValidatorWithoutInfo(*args, **kwargs)
```

## Methods

### `__call__`

```python
__call__(self, cls: 'type[_ModelType]', value: 'Any', handler: 'ModelWrapValidatorHandler[_ModelType]', /) -> '_ModelType'
```

Call self as a function.


### `__init__`

```python
__init__(self, *args, **kwargs)
```

