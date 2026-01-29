# validate_email

**Module:** `pydantic.networks`

## Signature

```python
validate_email(value: 'str') -> 'tuple[str, str]'
```

## Description

Email address validation using [email-validator](https://pypi.org/project/email-validator/).

Returns:
    A tuple containing the local part of the email (or the name for "pretty" email addresses)
        and the normalized email.

Raises:
    PydanticCustomError: If the email is invalid.

Note:
    Note that:

    * Raw IP address (literal) domain parts are not allowed.
    * `"John Doe <local_part@domain.com>"` style "pretty" email addresses are processed.
    * Spaces are striped from the beginning and end of addresses, but no error is raised.
