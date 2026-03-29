# validate_call

**Module:** `pydantic.validate_call_decorator`

## Signature

```python
validate_call(func: 'AnyCallableT | None' = None, /, *, config: 'ConfigDict | None' = None, validate_return: 'bool' = False) -> 'AnyCallableT | Callable[[AnyCallableT], AnyCallableT]'
```

## Description

!!! abstract "Usage Documentation"
    [Validation Decorator](../concepts/validation_decorator.md)

Returns a decorated wrapper around the function that validates the arguments and, optionally, the return value.

Usage may be either as a plain decorator `@validate_call` or with arguments `@validate_call(...)`.

Args:
    func: The function to be decorated.
    config: The configuration dictionary.
    validate_return: Whether to validate the return value.

Returns:
    The decorated function.
