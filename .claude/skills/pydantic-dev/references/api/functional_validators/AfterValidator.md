# AfterValidator

**Module:** `pydantic.functional_validators`

!!! abstract "Usage Documentation"
    [field *after* validators](../concepts/validators.md#field-after-validator)

A metadata class that indicates that a validation should be applied **after** the inner validation logic.

Attributes:
    func: The validator function.

Example:
    ```python
    from typing import Annotated

    from pydantic import AfterValidator, BaseModel, ValidationError

    MyInt = Annotated[int, AfterValidator(lambda v: v + 1)]

    class Model(BaseModel):
        a: MyInt

    print(Model(a=1).a)
    #> 2

    try:
        Model(a='a')
    except ValidationError as e:
        print(e.json(indent=2))
        '''
        [
          {
            "type": "int_parsing",
            "loc": [
              "a"
            ],
            "msg": "Input should be a valid integer, unable to parse string as an integer",
            "input": "a",
            "url": "https://errors.pydantic.dev/2/v/int_parsing"
          }
        ]
        '''
    ```

## Signature

```python
AfterValidator(func: 'core_schema.NoInfoValidatorFunction | core_schema.WithInfoValidatorFunction') -> None
```

## Methods

### `__get_pydantic_core_schema__`

```python
__get_pydantic_core_schema__(self, source_type: 'Any', handler: 'GetCoreSchemaHandler') -> 'core_schema.CoreSchema'
```


### `__init__`

```python
__init__(self, func: 'core_schema.NoInfoValidatorFunction | core_schema.WithInfoValidatorFunction') -> None
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

