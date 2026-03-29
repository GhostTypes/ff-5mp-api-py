# ImportString

**Module:** `pydantic.types`

A type that can be used to import a Python object from a string.

`ImportString` expects a string and loads the Python object importable at that dotted path.
Attributes of modules may be separated from the module by `:` or `.`, e.g. if `'math:cos'` is provided,
the resulting field value would be the function `cos`. If a `.` is used and both an attribute and submodule
are present at the same path, the module will be preferred.

On model instantiation, pointers will be evaluated and imported. There is
some nuance to this behavior, demonstrated in the examples below.

```python
import math

from pydantic import BaseModel, Field, ImportString, ValidationError

class ImportThings(BaseModel):
    obj: ImportString

# A string value will cause an automatic import
my_cos = ImportThings(obj='math.cos')

# You can use the imported function as you would expect
cos_of_0 = my_cos.obj(0)
assert cos_of_0 == 1

# A string whose value cannot be imported will raise an error
try:
    ImportThings(obj='foo.bar')
except ValidationError as e:
    print(e)
    '''
    1 validation error for ImportThings
    obj
      Invalid python path: No module named 'foo.bar' [type=import_error, input_value='foo.bar', input_type=str]
    '''

# Actual python objects can be assigned as well
my_cos = ImportThings(obj=math.cos)
my_cos_2 = ImportThings(obj='math.cos')
my_cos_3 = ImportThings(obj='math:cos')
assert my_cos == my_cos_2 == my_cos_3

# You can set default field value either as Python object:
class ImportThingsDefaultPyObj(BaseModel):
    obj: ImportString = math.cos

# or as a string value (but only if used with `validate_default=True`)
class ImportThingsDefaultString(BaseModel):
    obj: ImportString = Field(default='math.cos', validate_default=True)

my_cos_default1 = ImportThingsDefaultPyObj()
my_cos_default2 = ImportThingsDefaultString()
assert my_cos_default1.obj == my_cos_default2.obj == math.cos

# note: this will not work!
class ImportThingsMissingValidateDefault(BaseModel):
    obj: ImportString = 'math.cos'

my_cos_default3 = ImportThingsMissingValidateDefault()
assert my_cos_default3.obj == 'math.cos'  # just string, not evaluated
```

Serializing an `ImportString` type to json is also possible.

```python
from pydantic import BaseModel, ImportString

class ImportThings(BaseModel):
    obj: ImportString

# Create an instance
m = ImportThings(obj='math.cos')
print(m)
#> obj=<built-in function cos>
print(m.model_dump_json())
#> {"obj":"math.cos"}
```

## Signature

```python
ImportString()
```

## Methods

### `__class_getitem__`

```python
__class_getitem__(item: 'AnyType') -> 'AnyType'
```


### `__get_pydantic_core_schema__`

```python
__get_pydantic_core_schema__(source: 'type[Any]', handler: 'GetCoreSchemaHandler') -> 'core_schema.CoreSchema'
```


### `__get_pydantic_json_schema__`

```python
__get_pydantic_json_schema__(cs: 'CoreSchema', handler: 'GetJsonSchemaHandler') -> 'JsonSchemaValue'
```


### `__repr__`

```python
__repr__(self) -> 'str'
```

Return repr(self).

