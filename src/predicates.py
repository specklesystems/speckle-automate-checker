"""Configuration module defining mappings between spreadsheet predicates and rule methods."""

# Mapping of input predicates to the corresponding methods in PropertyRules
PREDICATE_METHOD_MAP = {
    "exists": "has_parameter",
    "matches": "is_parameter_value",
    "greater than": "is_parameter_value_greater_than",
    "less than": "is_parameter_value_less_than",
    "in range": "is_parameter_value_in_range",
    "in list": "is_parameter_value_in_list",
    "equals": "is_equal_value",
    "identical": "is_identical_value",
    "not equal": "is_not_equal_value",
    "not identical": "is_not_identical_value",
    "true": "is_parameter_value_true",
    "false": "is_parameter_value_false",
    "is like": "is_parameter_value_like",
}
