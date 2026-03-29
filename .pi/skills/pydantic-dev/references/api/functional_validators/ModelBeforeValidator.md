# ModelBeforeValidator

**Module:** `pydantic.functional_validators`

A `@model_validator` decorated function signature. This is used when `mode='before'`.

## Signature

```python
ModelBeforeValidator(*args, **kwargs)
```

## Methods

### `__call__`

```python
__call__(self, cls: 'Any', value: 'Any', info: 'core_schema.ValidationInfo[Any]', /) -> 'Any'
```

Call self as a function.


### `__init__`

```python
__init__(self, *args, **kwargs)
```

