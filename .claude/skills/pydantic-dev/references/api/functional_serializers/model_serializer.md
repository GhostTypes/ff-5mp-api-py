# model_serializer

**Module:** `pydantic.functional_serializers`

## Signature

```python
model_serializer(f: '_ModelPlainSerializerT | _ModelWrapSerializerT | None' = None, /, *, mode: "Literal['plain', 'wrap']" = 'plain', when_used: 'WhenUsed' = 'always', return_type: 'Any' = PydanticUndefined) -> '_ModelPlainSerializerT | Callable[[_ModelWrapSerializerT], _ModelWrapSerializerT] | Callable[[_ModelPlainSerializerT], _ModelPlainSerializerT]'
```

## Description

Decorator that enables custom model serialization.

This is useful when a model need to be serialized in a customized manner, allowing for flexibility beyond just specific fields.

An example would be to serialize temperature to the same temperature scale, such as degrees Celsius.

```python
from typing import Literal

from pydantic import BaseModel, model_serializer

class TemperatureModel(BaseModel):
    unit: Literal['C', 'F']
    value: int

    @model_serializer()
    def serialize_model(self):
        if self.unit == 'F':
            return {'unit': 'C', 'value': int((self.value - 32) / 1.8)}
        return {'unit': self.unit, 'value': self.value}

temperature = TemperatureModel(unit='F', value=212)
print(temperature.model_dump())
#> {'unit': 'C', 'value': 100}
```

Two signatures are supported for `mode='plain'`, which is the default:

- `(self)`
- `(self, info: SerializationInfo)`

And two other signatures for `mode='wrap'`:

- `(self, nxt: SerializerFunctionWrapHandler)`
- `(self, nxt: SerializerFunctionWrapHandler, info: SerializationInfo)`

    See [the usage documentation](../concepts/serialization.md#serializers) for more information.

Args:
    f: The function to be decorated.
    mode: The serialization mode.

        - `'plain'` means the function will be called instead of the default serialization logic
        - `'wrap'` means the function will be called with an argument to optionally call the default
            serialization logic.
    when_used: Determines when this serializer should be used.
    return_type: The return type for the function. If omitted it will be inferred from the type annotation.

Returns:
    The decorator function.
