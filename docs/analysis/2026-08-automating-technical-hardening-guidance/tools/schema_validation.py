"""Validate NIST schemas without rewriting Unicode property patterns."""

import regex
from jsonschema import FormatChecker, ValidationError, validators


def unicode_pattern(validator, pattern, instance, schema):
    """NIST uses Unicode properties such as \\p{L}, unsupported by Python re."""
    if validator.is_type(instance, "string") and not regex.search(pattern, instance):
        yield ValidationError(f"{instance!r} does not match {pattern!r}")


def schema_validator(schema):
    checker = FormatChecker()
    if not {"date-time", "uri"} <= checker.checkers.keys():
        raise RuntimeError("Install jsonschema[format] to enforce OSCAL date-time and URI formats")

    @checker.checks("regex", raises=regex.error)
    def valid_regex(value):
        if not isinstance(value, str):
            return True
        regex.compile(value)
        return True

    base = validators.validator_for(schema)
    base.check_schema(schema, format_checker=checker)
    validator = validators.extend(base, {"pattern": unicode_pattern})
    return validator(schema, format_checker=checker)