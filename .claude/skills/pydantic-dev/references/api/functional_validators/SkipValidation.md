# SkipValidation

**Module:** `pydantic.functional_validators`

If this is applied as an annotation (e.g., via `x: Annotated[int, SkipValidation]`), validation will be
    skipped. You can also use `SkipValidation[int]` as a shorthand for `Annotated[int, SkipValidation]`.

This can be useful if you want to use a type annotation for documentation/IDE/type-checking purposes,
and know that it is safe to skip validation for one or more of the fields.

Because this converts the validation schema to `any_schema`, subsequent annotation-applied transformations
may not have the expected effects. Therefore, when used, this annotation should generally be the final
annotation applied to a type.

## Signature

```python
SkipValidation() -> None
```

## Methods

### `__class_getitem__`

```python
__class_getitem__(item: 'Any') -> 'Any'
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

