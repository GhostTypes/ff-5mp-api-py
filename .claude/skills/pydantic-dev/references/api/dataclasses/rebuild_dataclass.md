# rebuild_dataclass

**Module:** `pydantic.dataclasses`

## Signature

```python
rebuild_dataclass(cls: 'type[PydanticDataclass]', *, force: 'bool' = False, raise_errors: 'bool' = True, _parent_namespace_depth: 'int' = 2, _types_namespace: 'MappingNamespace | None' = None) -> 'bool | None'
```

## Description

Try to rebuild the pydantic-core schema for the dataclass.

This may be necessary when one of the annotations is a ForwardRef which could not be resolved during
the initial attempt to build the schema, and automatic rebuilding fails.

This is analogous to `BaseModel.model_rebuild`.

Args:
    cls: The class to rebuild the pydantic-core schema for.
    force: Whether to force the rebuilding of the schema, defaults to `False`.
    raise_errors: Whether to raise errors, defaults to `True`.
    _parent_namespace_depth: The depth level of the parent namespace, defaults to 2.
    _types_namespace: The types namespace, defaults to `None`.

Returns:
    Returns `None` if the schema is already "complete" and rebuilding was not required.
    If rebuilding _was_ required, returns `True` if rebuilding was successful, otherwise `False`.
