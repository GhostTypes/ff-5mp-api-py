# BeforeValidator

**Module:** `pydantic.functional_validators`

!!! abstract "Usage Documentation"
    [field *before* validators](../concepts/validators.md#field-before-validator)

A metadata class that indicates that a validation should be applied **before** the inner validation logic.

Attributes:
    func: The validator function.
    json_schema_input_type: The input type used to generate the appropriate
        JSON Schema (in validation mode). The actual input type is `Any`.

Example:
    ```python
    from typing import Annotated

    from pydantic import BaseModel, BeforeValidator

    MyInt = Annotated[int, BeforeValidator(lambda v: v + 1)]

    class Model(BaseModel):
        a: MyInt

    print(Model(a=1).a)
    #> 2

    try:
        Model(a='a')
    except TypeError as e:
        print(e)
        #> can only concatenate str (not "int") to str
    ```

## Signature

```python
BeforeValidator(func: 'core_schema.NoInfoValidatorFunction | core_schema.WithInfoValidatorFunction', json_schema_input_type: 'Any' = PydanticUndefined) -> None
```

## Methods

### `__get_pydantic_core_schema__`

```python
__get_pydantic_core_schema__(self, source_type: 'Any', handler: 'GetCoreSchemaHandler') -> 'core_schema.CoreSchema'
```


### `__init__`

```python
__init__(self, func: 'core_schema.NoInfoValidatorFunction | core_schema.WithInfoValidatorFunction', json_schema_input_type: 'Any' = PydanticUndefined) -> None
```

Initialize self.  See help(type(self)) for accurate signature.


### `__replace__`

```python
__replace__(self, /, **changes)
```


### `__repr__`

```python
__repr__(self)
```

Return repr(self).


### `__setstate__`

```python
__setstate__(self, state)
```

