# field_validator

**Module:** `pydantic.functional_validators`

## Signature

```python
field_validator(field: 'str', /, *fields: 'str', mode: 'FieldValidatorModes' = 'after', check_fields: 'bool | None' = None, json_schema_input_type: 'Any' = PydanticUndefined) -> 'Callable[[Any], Any]'
```

## Description

!!! abstract "Usage Documentation"
    [field validators](../concepts/validators.md#field-validators)

Decorate methods on the class indicating that they should be used to validate fields.

Example usage:
```python
from typing import Any

from pydantic import (
    BaseModel,
    ValidationError,
    field_validator,
)

class Model(BaseModel):
    a: str

    @field_validator('a')
    @classmethod
    def ensure_foobar(cls, v: Any):
        if 'foobar' not in v:
            raise ValueError('"foobar" not found in a')
        return v

print(repr(Model(a='this is foobar good')))
#> Model(a='this is foobar good')

try:
    Model(a='snap')
except ValidationError as exc_info:
    print(exc_info)
    '''
    1 validation error for Model
    a
      Value error, "foobar" not found in a [type=value_error, input_value='snap', input_type=str]
    '''
```

For more in depth examples, see [Field Validators](../concepts/validators.md#field-validators).

Args:
    field: The first field the `field_validator` should be called on; this is separate
        from `fields` to ensure an error is raised if you don't pass at least one.
    *fields: Additional field(s) the `field_validator` should be called on.
    mode: Specifies whether to validate the fields before or after validation.
    check_fields: Whether to check that the fields actually exist on the model.
    json_schema_input_type: The input type of the function. This is only used to generate
        the appropriate JSON Schema (in validation mode) and can only specified
        when `mode` is either `'before'`, `'plain'` or `'wrap'`.

Returns:
    A decorator that can be used to decorate a function to be used as a field_validator.

Raises:
    PydanticUserError:
        - If `@field_validator` is used bare (with no fields).
        - If the args passed to `@field_validator` as fields are not strings.
        - If `@field_validator` applied to instance methods.
