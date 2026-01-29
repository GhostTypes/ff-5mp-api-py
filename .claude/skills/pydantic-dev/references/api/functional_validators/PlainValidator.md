# PlainValidator

**Module:** `pydantic.functional_validators`

!!! abstract "Usage Documentation"
    [field *plain* validators](../concepts/validators.md#field-plain-validator)

A metadata class that indicates that a validation should be applied **instead** of the inner validation logic.

!!! note
    Before v2.9, `PlainValidator` wasn't always compatible with JSON Schema generation for `mode='validation'`.
    You can now use the `json_schema_input_type` argument to specify the input type of the function
    to be used in the JSON schema when `mode='validation'` (the default). See the example below for more details.

Attributes:
    func: The validator function.
    json_schema_input_type: The input type used to generate the appropriate
        JSON Schema (in validation mode). The actual input type is `Any`.

Example:
    ```python
    from typing import Annotated, Union

    from pydantic import BaseModel, PlainValidator

    def validate(v: object) -> int:
        if not isinstance(v, (int, str)):
            raise ValueError(f'Expected int or str, go {type(v)}')

        return int(v) + 1

    MyInt = Annotated[
        int,
        PlainValidator(validate, json_schema_input_type=Union[str, int]),  # (1)!
    ]

    class Model(BaseModel):
        a: MyInt

    print(Model(a='1').a)
    #> 2

    print(Model(a=1).a)
    #> 2
    ```

    1. In this example, we've specified the `json_schema_input_type` as `Union[str, int]` which indicates to the JSON schema
    generator that in validation mode, the input type for the `a` field can be either a [`str`][] or an [`int`][].

## Signature

```python
PlainValidator(func: 'core_schema.NoInfoValidatorFunction | core_schema.WithInfoValidatorFunction', json_schema_input_type: 'Any' = typing.Any) -> None
```

## Methods

### `__get_pydantic_core_schema__`

```python
__get_pydantic_core_schema__(self, source_type: 'Any', handler: 'GetCoreSchemaHandler') -> 'core_schema.CoreSchema'
```


### `__init__`

```python
__init__(self, func: 'core_schema.NoInfoValidatorFunction | core_schema.WithInfoValidatorFunction', json_schema_input_type: 'Any' = typing.Any) -> None
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

