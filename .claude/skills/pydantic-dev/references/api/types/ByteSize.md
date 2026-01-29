# ByteSize

**Module:** `pydantic.types`

Converts a string representing a number of bytes with units (such as `'1KB'` or `'11.5MiB'`) into an integer.

You can use the `ByteSize` data type to (case-insensitively) convert a string representation of a number of bytes into
an integer, and also to print out human-readable strings representing a number of bytes.

In conformance with [IEC 80000-13 Standard](https://en.wikipedia.org/wiki/ISO/IEC_80000) we interpret `'1KB'` to mean 1000 bytes,
and `'1KiB'` to mean 1024 bytes. In general, including a middle `'i'` will cause the unit to be interpreted as a power of 2,
rather than a power of 10 (so, for example, `'1 MB'` is treated as `1_000_000` bytes, whereas `'1 MiB'` is treated as `1_048_576` bytes).

!!! info
    Note that `1b` will be parsed as "1 byte" and not "1 bit".

```python
from pydantic import BaseModel, ByteSize

class MyModel(BaseModel):
    size: ByteSize

print(MyModel(size=52000).size)
#> 52000
print(MyModel(size='3000 KiB').size)
#> 3072000

m = MyModel(size='50 PB')
print(m.size.human_readable())
#> 44.4PiB
print(m.size.human_readable(decimal=True))
#> 50.0PB
print(m.size.human_readable(separator=' '))
#> 44.4 PiB

print(m.size.to('TiB'))
#> 45474.73508864641
```

## Methods

### `__get_pydantic_core_schema__`

```python
__get_pydantic_core_schema__(source: 'type[Any]', handler: 'GetCoreSchemaHandler') -> 'core_schema.CoreSchema'
```


### `human_readable`

```python
human_readable(self, decimal: 'bool' = False, separator: 'str' = '') -> 'str'
```

Converts a byte size to a human readable string.

Args:
    decimal: If True, use decimal units (e.g. 1000 bytes per KB). If False, use binary units
        (e.g. 1024 bytes per KiB).
    separator: A string used to split the value and unit. Defaults to an empty string ('').

Returns:
    A human readable string representation of the byte size.


### `to`

```python
to(self, unit: 'str') -> 'float'
```

Converts a byte size to another unit, including both byte and bit units.

Args:
    unit: The unit to convert to. Must be one of the following: B, KB, MB, GB, TB, PB, EB,
        KiB, MiB, GiB, TiB, PiB, EiB (byte units) and
        bit, kbit, mbit, gbit, tbit, pbit, ebit,
        kibit, mibit, gibit, tibit, pibit, eibit (bit units).

Returns:
    The byte size in the new unit.

