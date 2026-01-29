# model_validator

**Module:** `pydantic.functional_validators`

## Signature

```python
model_validator(*, mode: "Literal['wrap', 'before', 'after']") -> 'Any'
```

## Description

!!! abstract "Usage Documentation"
    [Model Validators](../concepts/validators.md#model-validators)

Decorate model methods for validation purposes.

Example usage:
```python
from typing_extensions import Self

from pydantic import BaseModel, ValidationError, model_validator

class Square(BaseModel):
    width: float
    height: float

    @model_validator(mode='after')
    def verify_square(self) -> Self:
        if self.width != self.height:
            raise ValueError('width and height do not match')
        return self

s = Square(width=1, height=1)
print(repr(s))
#> Square(width=1.0, height=1.0)

try:
    Square(width=1, height=2)
except ValidationError as e:
    print(e)
    '''
    1 validation error for Square
      Value error, width and height do not match [type=value_error, input_value={'width': 1, 'height': 2}, input_type=dict]
    '''
```

For more in depth examples, see [Model Validators](../concepts/validators.md#model-validators).

Args:
    mode: A required string literal that specifies the validation mode.
        It can be one of the following: 'wrap', 'before', or 'after'.

Returns:
    A decorator that can be used to decorate a function to be used as a model validator.
