---
name: pydantic-dev
description: Professional Pydantic v2.12 development for data validation, serialization, and type-safe models. Use when working with Pydantic for (1) creating or modifying BaseModel classes, (2) implementing validators and serializers, (3) configuring model behavior, (4) handling JSON schema generation, (5) working with settings management, (6) debugging validation errors, (7) integrating with ORMs or APIs, or (8) any production-grade Python data validation tasks. Includes complete API reference, concept guides, examples, and migration patterns.
---

# Pydantic Professional Development

Comprehensive guidance for building production-ready applications with Pydantic v2.12, the most widely used data validation library for Python.

## Quick Reference

**Installation:** See `references/install.md` for setup instructions and optional dependencies

**Core Philosophy:** See `references/why.md` for Pydantic's design principles and when to use it

**Migration from v1:** See `references/migration.md` for upgrading from Pydantic v1.x

## Core Concepts

Pydantic uses Python type hints to define data schemas and performs validation/coercion automatically. The fundamental building blocks are:

### Models

**Primary documentation:** `references/concepts/models.md`

Define data structures by inheriting from `BaseModel`:

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    id: int
    name: str = Field(min_length=1, max_length=100)
    email: str
    age: int | None = None
```

**Key concepts:**
- Basic model usage and instantiation
- Data conversion and coercion
- Nested models and relationships
- Model methods: `model_validate()`, `model_dump()`, `model_dump_json()`
- Generic models and dynamic creation
- Immutability with `frozen=True`

**API reference:** `references/api/base_model/BaseModel.md` - Complete BaseModel class documentation

### Fields

**Primary documentation:** `references/concepts/fields.md`

Customize field behavior with constraints, defaults, and metadata:

```python
from pydantic import BaseModel, Field
from typing import Annotated

class Product(BaseModel):
    name: str = Field(description="Product name")
    price: Annotated[float, Field(gt=0, description="Price in USD")]
    quantity: int = Field(default=0, ge=0)
```

**Key concepts:**
- Field constraints (gt, ge, lt, le, min_length, max_length, pattern)
- Default values and factories
- Aliases and validation aliases
- Required vs optional fields
- Computed fields with `@computed_field`

**API reference:** `references/api/fields/` - Field, FieldInfo, and computed field APIs

### Validators

**Primary documentation:** `references/concepts/validators.md`

Implement custom validation logic with field and model validators:

```python
from pydantic import BaseModel, field_validator, model_validator

class Account(BaseModel):
    username: str
    password: str
    password_confirm: str

    @field_validator('username')
    @classmethod
    def username_alphanumeric(cls, v):
        assert v.isalnum(), 'must be alphanumeric'
        return v

    @model_validator(mode='after')
    def check_passwords_match(self):
        if self.password != self.password_confirm:
            raise ValueError('passwords do not match')
        return self
```

**Validator types:**
- **After validators:** Run after Pydantic validation (type-safe, recommended)
- **Before validators:** Run before validation (for data preprocessing)
- **Wrap validators:** Full control over validation process
- **Plain validators:** Replace default validation entirely

**API reference:** `references/api/functional_validators/` - All validator APIs and decorators

### Types

**Primary documentation:** `references/concepts/types.md`

Pydantic supports all Python types plus specialized validation types:

**Standard types:** `int`, `float`, `str`, `bool`, `list`, `dict`, `set`, `tuple`, `datetime`, `date`, `time`, `UUID`, etc.

**Pydantic types:** See `references/api/types/` for specialized types:
- Constrained types: `conint()`, `constr()`, `confloat()`, etc.
- Network types: `EmailStr`, `AnyUrl`, `IPvAnyAddress`
- Datetime types: `AwareDatetime`, `NaiveDatetime`, `FutureDate`, `PastDate`
- Special types: `Json`, `SecretStr`, `PaymentCardNumber`, `FilePath`, `DirectoryPath`

**Type documentation:** `references/concepts/types.md` covers all supported types and patterns

### Configuration

**Primary documentation:** `references/concepts/config.md`

Control model behavior with `ConfigDict`:

```python
from pydantic import BaseModel, ConfigDict

class User(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        frozen=False,
        extra='forbid'
    )
```

**Common settings:**
- `extra`: 'forbid' | 'allow' | 'ignore' - Handle extra fields
- `validate_assignment`: Validate on attribute assignment
- `frozen`: Make instances immutable
- `str_strip_whitespace`: Strip whitespace from strings
- `from_attributes`: Enable ORM mode for SQLAlchemy, etc.
- `populate_by_name`: Allow population by field name and alias

**API reference:** `references/api/config/ConfigDict.md`

## Common Workflows

### Validation Workflows

**Parse untrusted data:**
```python
user = User.model_validate(data)  # Raises ValidationError if invalid
```

**Parse JSON:**
```python
user = User.model_validate_json(json_string)
```

**Create without validation:**
```python
user = User.model_construct(**trusted_data)  # Skip validation for performance
```

**Handle validation errors:** See `references/errors/validation_errors.md`

### Serialization Workflows

**Primary documentation:** `references/concepts/serialization.md`

**Export to dict:**
```python
user_dict = user.model_dump()
user_dict = user.model_dump(exclude={'password'})
user_dict = user.model_dump(by_alias=True)
```

**Export to JSON:**
```python
json_str = user.model_dump_json()
json_str = user.model_dump_json(indent=2, exclude_none=True)
```

**Custom serializers:** See `references/api/functional_serializers/`

### JSON Schema Generation

**Primary documentation:** `references/concepts/json_schema.md`

**Generate schema:**
```python
schema = User.model_json_schema()
schema = User.model_json_schema(by_alias=True, mode='serialization')
```

**Customize schema generation:** See `references/api/json_schema/GenerateJsonSchema.md`

### Settings Management

**Primary documentation:** `references/concepts/pydantic_settings.md`

For application configuration from environment variables:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    api_key: str
    debug: bool = False

    model_config = ConfigDict(env_file='.env')

settings = Settings()
```

**API reference:** `references/api/pydantic_settings/`

### Working with ORMs

**Primary documentation:** `references/examples/orms.md`

Pydantic integrates with SQLAlchemy, Django, and other ORMs:

```python
from pydantic import BaseModel, ConfigDict

class UserModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str

# Convert ORM instance to Pydantic model
user = UserModel.model_validate(sql_user)
```

## Advanced Features

### Dataclasses

**Primary documentation:** `references/concepts/dataclasses.md`

Use Pydantic with Python dataclasses:

```python
from pydantic.dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str
```

**API reference:** `references/api/dataclasses/`

### Type Adapter

**Primary documentation:** `references/concepts/type_adapter.md`

Validate data against any type, not just models:

```python
from pydantic import TypeAdapter

ListOfInts = TypeAdapter(list[int])
validated = ListOfInts.validate_python(['1', '2', '3'])
```

**API reference:** `references/api/type_adapter/TypeAdapter.md`

### Unions and Discriminated Unions

**Primary documentation:** `references/concepts/unions.md`

Handle multiple possible types:

```python
from typing import Literal, Union
from pydantic import BaseModel, Field

class Cat(BaseModel):
    pet_type: Literal['cat']
    meows: int

class Dog(BaseModel):
    pet_type: Literal['dog']
    barks: float

class Owner(BaseModel):
    pet: Union[Cat, Dog] = Field(discriminator='pet_type')
```

### Aliases

**Primary documentation:** `references/concepts/alias.md`

Map field names for validation and serialization:

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    username: str = Field(alias='userName')
```

**API reference:** `references/api/aliases/`

### Strict Mode

**Primary documentation:** `references/concepts/strict_mode.md`

Enforce strict type validation without coercion:

```python
from pydantic import BaseModel, ConfigDict

class StrictModel(BaseModel):
    model_config = ConfigDict(strict=True)

    count: int  # Won't accept '123', only 123
```

### Performance Optimization

**Primary documentation:** `references/concepts/performance.md`

Guidelines for optimizing Pydantic performance in production

## Error Handling

### Validation Errors

**Complete reference:** `references/errors/validation_errors.md`

Understand and handle validation errors:

```python
from pydantic import ValidationError

try:
    user = User(**data)
except ValidationError as e:
    print(e.errors())  # List of error dictionaries
    print(e.json())    # JSON formatted errors
```

**Error types reference:** `references/errors/errors.md` - All validation error codes

### Usage Errors

**Reference:** `references/errors/usage_errors.md`

Common mistakes and how to fix them

## API Reference

Complete API documentation organized by module:

- **`references/api/base_model/`** - BaseModel class and create_model()
- **`references/api/fields/`** - Field(), FieldInfo, computed fields, private attributes
- **`references/api/config/`** - ConfigDict and configuration options
- **`references/api/types/`** - All Pydantic types (constrained types, network types, etc.)
- **`references/api/functional_validators/`** - Validator decorators and classes
- **`references/api/functional_serializers/`** - Serializer decorators and classes
- **`references/api/json_schema/`** - JSON schema generation APIs
- **`references/api/dataclasses/`** - Pydantic dataclass support
- **`references/api/type_adapter/`** - TypeAdapter for validating any type
- **`references/api/errors/`** - Error classes
- **`references/api/networks/`** - Network validation types (URLs, emails, IPs)
- **`references/api/aliases/`** - Alias configuration classes
- **`references/api/validate_call/`** - Function validation decorator
- **`references/api/version/`** - Version information

## Examples

Practical examples for common use cases:

- **`references/examples/custom_validators.md`** - Building custom validators
- **`references/examples/orms.md`** - Integration with SQLAlchemy and Django
- **`references/examples/files.md`** - Validating file data (JSON, CSV, etc.)
- **`references/examples/requests.md`** - Validating API requests and responses
- **`references/examples/queues.md`** - Using Pydantic with message queues
- **`references/examples/dynamic_models.md`** - Creating models at runtime

## Development Guidelines

### Code Quality

**Linting integration:** `references/integrations/linting.md` - Configure ruff, mypy, and other linters

**Best practices:**
- Always type annotate fields explicitly
- Use `Field()` for constraints and metadata
- Prefer after validators over before validators
- Use discriminated unions for type safety
- Enable `validate_assignment` for mutable models
- Use `frozen=True` for immutable data
- Configure `extra='forbid'` to catch typos

### Production Readiness

**Required considerations:**
1. **Error handling:** Always catch and handle `ValidationError`
2. **Performance:** Use `model_construct()` for trusted data
3. **Security:** Validate all external inputs
4. **Serialization:** Test `model_dump()` output matches expectations
5. **Schema validation:** Generate and validate JSON schemas for APIs
6. **Migration:** Follow `references/migration.md` when upgrading

### Testing

**Validate your models:**
```python
def test_user_validation():
    # Test valid data
    user = User(id=1, name="Test", email="test@example.com")
    assert user.id == 1

    # Test invalid data
    with pytest.raises(ValidationError):
        User(id="invalid", name="Test")
```

## Getting Help

- **Overview:** `references/index.md` - Introduction to Pydantic
- **Help resources:** `references/help_with_pydantic.md` - Community support
- **Version policy:** `references/version-policy.md` - Versioning and deprecation
- **Contributing:** `references/contributing.md` - How to contribute to Pydantic

## Version Information

This skill covers **Pydantic v2.12.5** (December 2025). For migration from v1.x, see `references/migration.md`.
