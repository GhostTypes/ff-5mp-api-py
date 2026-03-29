# PaymentCardNumber

**Module:** `pydantic.types`

Based on: https://en.wikipedia.org/wiki/Payment_card_number.

## Signature

```python
PaymentCardNumber(card_number: 'str')
```

## Methods

### `__get_pydantic_core_schema__`

```python
__get_pydantic_core_schema__(source: 'type[Any]', handler: 'GetCoreSchemaHandler') -> 'core_schema.CoreSchema'
```


### `__init__`

```python
__init__(self, card_number: 'str')
```

Initialize self.  See help(type(self)) for accurate signature.


### `validate`

```python
validate(input_value: 'str', /, _: 'core_schema.ValidationInfo') -> 'PaymentCardNumber'
```

Validate the card number and return a `PaymentCardNumber` instance.


### `validate_brand`

```python
validate_brand(card_number: 'str') -> 'PaymentCardBrand'
```

Validate length based on BIN for major brands:
https://en.wikipedia.org/wiki/Payment_card_number#Issuer_identification_number_(IIN).


### `validate_digits`

```python
validate_digits(card_number: 'str') -> 'None'
```

Validate that the card number is all digits.


### `validate_luhn_check_digit`

```python
validate_luhn_check_digit(card_number: 'str') -> 'str'
```

Based on: https://en.wikipedia.org/wiki/Luhn_algorithm.


## Properties

### `masked`

Mask all but the last 4 digits of the card number.

Returns:
    A masked card number string.

