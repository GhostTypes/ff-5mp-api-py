# SkipJsonSchema

**Module:** `pydantic.json_schema`

!!! abstract "Usage Documentation"
    [`SkipJsonSchema` Annotation](../concepts/json_schema.md#skipjsonschema-annotation)

Add this as an annotation on a field to skip generating a JSON schema for that field.

Example:
    ```python
    from pprint import pprint
    from typing import Union

    from pydantic import BaseModel
    from pydantic.json_schema import SkipJsonSchema

    class Model(BaseModel):
        a: Union[int, None] = None  # (1)!
        b: Union[int, SkipJsonSchema[None]] = None  # (2)!
        c: SkipJsonSchema[Union[int, None]] = None  # (3)!

    pprint(Model.model_json_schema())
    '''
    {
        'properties': {
            'a': {
                'anyOf': [
                    {'type': 'integer'},
                    {'type': 'null'}
                ],
                'default': None,
                'title': 'A'
            },
            'b': {
                'default': None,
                'title': 'B',
                'type': 'integer'
            }
        },
        'title': 'Model',
        'type': 'object'
    }
    '''
    ```

    1. The integer and null types are both included in the schema for `a`.
    2. The integer type is the only type included in the schema for `b`.
    3. The entirety of the `c` field is omitted from the schema.

## Signature

```python
SkipJsonSchema() -> None
```

## Methods

### `__class_getitem__`

```python
__class_getitem__(item: 'AnyType') -> 'AnyType'
```


### `__get_pydantic_json_schema__`

```python
__get_pydantic_json_schema__(self, core_schema: 'CoreSchema', handler: 'GetJsonSchemaHandler') -> 'JsonSchemaValue'
```


### `__init__`

```python
__init__(self) -> None
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

