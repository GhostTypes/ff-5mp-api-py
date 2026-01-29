# ModelBeforeValidatorWithoutInfo

**Module:** `pydantic.functional_validators`

A `@model_validator` decorated function signature.
This is used when `mode='before'` and the function does not have info argument.

## Signature

```python
ModelBeforeValidatorWithoutInfo(*args, **kwargs)
```

## Methods

### `__call__`

```python
__call__(self, cls: 'Any', value: 'Any', /) -> 'Any'
```

Call self as a function.


### `__init__`

```python
__init__(self, *args, **kwargs)
```

