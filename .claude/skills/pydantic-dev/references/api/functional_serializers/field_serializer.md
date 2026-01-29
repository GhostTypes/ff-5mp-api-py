# field_serializer

**Module:** `pydantic.functional_serializers`

## Signature

```python
field_serializer(*fields: 'str', mode: "Literal['plain', 'wrap']" = 'plain', return_type: 'Any' = PydanticUndefined, when_used: 'WhenUsed' = 'always', check_fields: 'bool | None' = None) -> 'Callable[[_FieldWrapSerializerT], _FieldWrapSerializerT] | Callable[[_FieldPlainSerializerT], _FieldPlainSerializerT]'
```

## Description

Decorator that enables custom field serialization.

In the below example, a field of type `set` is used to mitigate duplication. A `field_serializer` is used to serialize the data as a sorted list.

```python
from pydantic import BaseModel, field_serializer

class StudentModel(BaseModel):
    name: str = 'Jane'
    courses: set[str]

    @field_serializer('courses', when_used='json')
    def serialize_courses_in_order(self, courses: set[str]):
        return sorted(courses)

student = StudentModel(courses={'Math', 'Chemistry', 'English'})
print(student.model_dump_json())
#> {"name":"Jane","courses":["Chemistry","English","Math"]}
```

See [the usage documentation](../concepts/serialization.md#serializers) for more information.

Four signatures are supported:

- `(self, value: Any, info: FieldSerializationInfo)`
- `(self, value: Any, nxt: SerializerFunctionWrapHandler, info: FieldSerializationInfo)`
- `(value: Any, info: SerializationInfo)`
- `(value: Any, nxt: SerializerFunctionWrapHandler, info: SerializationInfo)`

Args:
    fields: Which field(s) the method should be called on.
    mode: The serialization mode.

        - `plain` means the function will be called instead of the default serialization logic,
        - `wrap` means the function will be called with an argument to optionally call the
           default serialization logic.
    return_type: Optional return type for the function, if omitted it will be inferred from the type annotation.
    when_used: Determines the serializer will be used for serialization.
    check_fields: Whether to check that the fields actually exist on the model.

Returns:
    The decorator function.
