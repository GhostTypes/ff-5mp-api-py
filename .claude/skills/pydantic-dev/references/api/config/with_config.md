# with_config

**Module:** `pydantic.config`

## Signature

```python
with_config(config: 'ConfigDict | None' = None, /, **kwargs: 'Any') -> 'Callable[[_TypeT], _TypeT]'
```

## Description

!!! abstract "Usage Documentation"
    [Configuration with other types](../concepts/config.md#configuration-on-other-supported-types)

A convenience decorator to set a [Pydantic configuration](config.md) on a `TypedDict` or a `dataclass` from the standard library.

Although the configuration can be set using the `__pydantic_config__` attribute, it does not play well with type checkers,
especially with `TypedDict`.

!!! example "Usage"

    ```python
    from typing_extensions import TypedDict

    from pydantic import ConfigDict, TypeAdapter, with_config

    @with_config(ConfigDict(str_to_lower=True))
    class TD(TypedDict):
        x: str

    ta = TypeAdapter(TD)

    print(ta.validate_python({'x': 'ABC'}))
    #> {'x': 'abc'}
    ```

/// deprecated-removed | v2.11 v3
Passing `config` as a keyword argument.
///

/// version-changed | v2.11
Keyword arguments can be provided directly instead of a config dictionary.
///
