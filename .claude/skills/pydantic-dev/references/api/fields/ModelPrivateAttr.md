# ModelPrivateAttr

**Module:** `pydantic.fields`

A descriptor for private attributes in class models.

!!! warning
    You generally shouldn't be creating `ModelPrivateAttr` instances directly, instead use
    `pydantic.fields.PrivateAttr`. (This is similar to `FieldInfo` vs. `Field`.)

Attributes:
    default: The default value of the attribute if not provided.
    default_factory: A callable function that generates the default value of the
        attribute if not provided.

## Signature

```python
ModelPrivateAttr(default: 'Any' = PydanticUndefined, *, default_factory: 'Callable[[], Any] | None' = None) -> 'None'
```

## Methods

### `__getattr__`

```python
__getattr__(self, item: 'str') -> 'Any'
```

This function improves compatibility with custom descriptors by ensuring delegation happens
as expected when the default value of a private attribute is a descriptor.


### `__init__`

```python
__init__(self, default: 'Any' = PydanticUndefined, *, default_factory: 'Callable[[], Any] | None' = None) -> 'None'
```

Initialize self.  See help(type(self)) for accurate signature.


### `__pretty__`

```python
__pretty__(self, fmt: 'Callable[[Any], Any]', **kwargs: 'Any') -> 'Generator[Any]'
```

Used by devtools (https://python-devtools.helpmanual.io/) to pretty print objects.


### `__repr__`

```python
__repr__(self) -> 'str'
```

Return repr(self).


### `__repr_args__`

```python
__repr_args__(self) -> 'ReprArgs'
```

Returns the attributes to show in __str__, __repr__, and __pretty__ this is generally overridden.

Can either return:
* name - value pairs, e.g.: `[('foo_name', 'foo'), ('bar_name', ['b', 'a', 'r'])]`
* or, just values, e.g.: `[(None, 'foo'), (None, ['b', 'a', 'r'])]`


### `__repr_name__`

```python
__repr_name__(self) -> 'str'
```

Name of the instance's class, used in __repr__.


### `__repr_recursion__`

```python
__repr_recursion__(self, object: 'Any') -> 'str'
```

Returns the string representation of a recursive object.


### `__repr_str__`

```python
__repr_str__(self, join_str: 'str') -> 'str'
```


### `__rich_repr__`

```python
__rich_repr__(self) -> 'RichReprResult'
```

Used by Rich (https://rich.readthedocs.io/en/stable/pretty.html) to pretty print objects.


### `__set_name__`

```python
__set_name__(self, cls: 'type[Any]', name: 'str') -> 'None'
```

Preserve `__set_name__` protocol defined in https://peps.python.org/pep-0487.


### `__str__`

```python
__str__(self) -> 'str'
```

Return str(self).


### `get_default`

```python
get_default(self) -> 'Any'
```

Retrieve the default value of the object.

If `self.default_factory` is `None`, the method will return a deep copy of the `self.default` object.

If `self.default_factory` is not `None`, it will call `self.default_factory` and return the value returned.

Returns:
    The default value of the object.

