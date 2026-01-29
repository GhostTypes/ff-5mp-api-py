# InstanceOf

**Module:** `pydantic.functional_validators`

Generic type for annotating a type that is an instance of a given class.

Example:
    ```python
    from pydantic import BaseModel, InstanceOf

    class Foo:
        ...

    class Bar(BaseModel):
        foo: InstanceOf[Foo]

    Bar(foo=Foo())
    try:
        Bar(foo=42)
    except ValidationError as e:
        print(e)
        """
        [
        │   {
        │   │   'type': 'is_instance_of',
        │   │   'loc': ('foo',),
        │   │   'msg': 'Input should be an instance of Foo',
        │   │   'input': 42,
        │   │   'ctx': {'class': 'Foo'},
        │   │   'url': 'https://errors.pydantic.dev/0.38.0/v/is_instance_of'
        │   }
        ]
        """
    ```

## Signature

```python
InstanceOf() -> None
```

## Methods

### `__class_getitem__`

```python
__class_getitem__(item: 'AnyType') -> 'AnyType'
```


### `__get_pydantic_core_schema__`

```python
__get_pydantic_core_schema__(source: 'Any', handler: 'GetCoreSchemaHandler') -> 'core_schema.CoreSchema'
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

