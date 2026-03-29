# dataclass

**Module:** `pydantic.dataclasses`

## Signature

```python
dataclass(_cls: 'type[_T] | None' = None, *, init: 'Literal[False]' = False, repr: 'bool' = True, eq: 'bool' = True, order: 'bool' = False, unsafe_hash: 'bool' = False, frozen: 'bool | None' = None, config: 'ConfigDict | type[object] | None' = None, validate_on_init: 'bool | None' = None, kw_only: 'bool' = False, slots: 'bool' = False) -> 'Callable[[type[_T]], type[PydanticDataclass]] | type[PydanticDataclass]'
```

## Description

!!! abstract "Usage Documentation"
    [`dataclasses`](../concepts/dataclasses.md)

A decorator used to create a Pydantic-enhanced dataclass, similar to the standard Python `dataclass`,
but with added validation.

This function should be used similarly to `dataclasses.dataclass`.

Args:
    _cls: The target `dataclass`.
    init: Included for signature compatibility with `dataclasses.dataclass`, and is passed through to
        `dataclasses.dataclass` when appropriate. If specified, must be set to `False`, as pydantic inserts its
        own  `__init__` function.
    repr: A boolean indicating whether to include the field in the `__repr__` output.
    eq: Determines if a `__eq__` method should be generated for the class.
    order: Determines if comparison magic methods should be generated, such as `__lt__`, but not `__eq__`.
    unsafe_hash: Determines if a `__hash__` method should be included in the class, as in `dataclasses.dataclass`.
    frozen: Determines if the generated class should be a 'frozen' `dataclass`, which does not allow its
        attributes to be modified after it has been initialized. If not set, the value from the provided `config` argument will be used (and will default to `False` otherwise).
    config: The Pydantic config to use for the `dataclass`.
    validate_on_init: A deprecated parameter included for backwards compatibility; in V2, all Pydantic dataclasses
        are validated on init.
    kw_only: Determines if `__init__` method parameters must be specified by keyword only. Defaults to `False`.
    slots: Determines if the generated class should be a 'slots' `dataclass`, which does not allow the addition of
        new attributes after instantiation.

Returns:
    A decorator that accepts a class as its argument and returns a Pydantic `dataclass`.

Raises:
    AssertionError: Raised if `init` is not `False` or `validate_on_init` is `False`.
