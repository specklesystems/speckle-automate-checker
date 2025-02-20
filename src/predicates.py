"""Configuration module defining mappings between spreadsheet predicates and rule methods."""

from src.rules import PropertyRules

# Mapping of input predicates to the corresponding methods in PropertyRules
PREDICATE_METHOD_MAP = {
    "exists": PropertyRules.has_parameter.__name__,
    "greater than": PropertyRules.is_parameter_value_greater_than.__name__,
    "less than": PropertyRules.is_parameter_value_less_than.__name__,
    "in range": PropertyRules.is_parameter_value_in_range.__name__,
    "in list": PropertyRules.is_parameter_value_in_list.__name__,
    "equal to": PropertyRules.is_equal_value.__name__,
    "not equal to": PropertyRules.is_not_equal_value.__name__,
    "is true": PropertyRules.is_parameter_value_true.__name__,
    "is false": PropertyRules.is_parameter_value_false.__name__,
    "is like": PropertyRules.is_parameter_value_like.__name__,
    "identical to": PropertyRules.is_identical_value.__name__,
    "contains": PropertyRules.is_parameter_value_containing.__name__,
    "does not contain": PropertyRules.is_parameter_value_not_containing.__name__,
}
