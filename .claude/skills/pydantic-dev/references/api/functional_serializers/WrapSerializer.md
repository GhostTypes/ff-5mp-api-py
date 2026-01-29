# WrapSerializer

**Module:** `pydantic.functional_serializers`

Wrap serializers receive the raw inputs along with a handler function that applies the standard serialization
logic, and can modify the resulting value before returning it as the final output of serialization.

For example, here's a scenario in which a wrap serializer transforms timezones to UTC **and** utilizes the existing `datetime` serialization logic.

```python
from datetime import datetime, timezone
from typing import Annotated, Any

from pydantic import BaseModel, WrapSerializer

class EventDatetime(BaseModel):
    start: datetime
    end: datetime

def convert_to_utc(value: Any, handler, info) -> dict[str, datetime]:
    # Note that `handler` can actually help serialize the `value` for
    # further custom serialization in case it's a subclass.
    partial_result = handler(value, info)
    if info.mode == 'json':
        return {
            k: datetime.fromisoformat(v).astimezone(timezone.utc)
            for k, v in partial_result.items()
        }
    return {k: v.astimezone(timezone.utc) for k, v in partial_result.items()}

UTCEventDatetime = Annotated[EventDatetime, WrapSerializer(convert_to_utc)]

class EventModel(BaseModel):
    event_datetime: UTCEventDatetime

dt = EventDatetime(
    start='2024-01-01T07:00:00-08:00', end='2024-01-03T20:00:00+06:00'
)
event = EventModel(event_datetime=dt)
print(event.model_dump())
'''
{
    'event_datetime': {
        'start': datetime.datetime(
            2024, 1, 1, 15, 0, tzinfo=datetime.timezone.utc
        ),
        'end': datetime.datetime(
            2024, 1, 3, 14, 0, tzinfo=datetime.timezone.utc
        ),
    }
}
'''

print(event.model_dump_json())
'''
{"event_datetime":{"start":"2024-01-01T15:00:00Z","end":"2024-01-03T14:00:00Z"}}
'''
```

Attributes:
    func: The serializer function to be wrapped.
    return_type: The return type for the function. If omitted it will be inferred from the type annotation.
    when_used: Determines when this serializer should be used. Accepts a string with values `'always'`,
        `'unless-none'`, `'json'`, and `'json-unless-none'`. Defaults to 'always'.

## Signature

```python
WrapSerializer(func: 'core_schema.WrapSerializerFunction', return_type: 'Any' = PydanticUndefined, when_used: 'WhenUsed' = 'always') -> None
```

## Methods

### `__get_pydantic_core_schema__`

```python
__get_pydantic_core_schema__(self, source_type: 'Any', handler: 'GetCoreSchemaHandler') -> 'core_schema.CoreSchema'
```

This method is used to get the Pydantic core schema of the class.

Args:
    source_type: Source type.
    handler: Core schema handler.

Returns:
    The generated core schema of the class.


### `__init__`

```python
__init__(self, func: 'core_schema.WrapSerializerFunction', return_type: 'Any' = PydanticUndefined, when_used: 'WhenUsed' = 'always') -> None
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

