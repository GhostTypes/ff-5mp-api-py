# ValidateAs

**Module:** `pydantic.functional_validators`

A helper class to validate a custom type from a type that is natively supported by Pydantic.

Args:
    from_type: The type natively supported by Pydantic to use to perform validation.
    instantiation_hook: A callable taking the validated type as an argument, and returning
        the populated custom type.

Example:
    ```python {lint="skip"}
    from typing import Annotated

    from pydantic import BaseModel, TypeAdapter, ValidateAs

    class MyCls:
        def __init__(self, a: int) -> None:
            self.a = a

        def __repr__(self) -> str:
            return f"MyCls(a={self.a})"

    class Model(BaseModel):
        a: int


    ta = TypeAdapter(
        Annotated[MyCls, ValidateAs(Model, lambda v: MyCls(a=v.a))]
    )

    print(ta.validate_python({'a': 1}))
    #> MyCls(a=1)
    ```

## Signature

```python
ValidateAs(from_type: 'type[_FromTypeT]', /, instantiation_hook: 'Callable[[_FromTypeT], Any]') -> 'None'
```

## Methods

### `__get_pydantic_core_schema__`

```python
__get_pydantic_core_schema__(self, source: 'Any', handler: 'GetCoreSchemaHandler') -> 'core_schema.CoreSchema'
```


### `__init__`

```python
__init__(self, from_type: 'type[_FromTypeT]', /, instantiation_hook: 'Callable[[_FromTypeT], Any]') -> 'None'
```

Initialize self.  See help(type(self)) for accurate signature.

