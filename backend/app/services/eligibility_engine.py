"""
Deterministic rule-based eligibility engine.

Given a user's profile data and a scheme's list of eligibility rules,
this module decides whether the user is eligible - using plain Python
comparisons, with NO AI/LLM involvement. This is intentional: eligibility
decisions must be explainable and reproducible.
"""
import operator

OPERATORS = {
    ">=": operator.ge,
    "<=": operator.le,
    ">": operator.gt,
    "<": operator.lt,
    "==": operator.eq,
    "!=": operator.ne,
}


def _coerce(value):
    """Try to treat a value as a number; fall back to lowercase text."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return str(value).strip().lower()


def check_eligibility(profile_data, rules):
    """
    Evaluate a user's profile against a scheme's eligibility rules.

    profile_data: dict, e.g. {"age": 22, "income": 300000, "state": "Madhya Pradesh"}
    rules: list of dicts, each with "field_name", "operator", "expected_value"

    Returns: {"eligible": bool, "matched_rules": [...], "failed_rules": [...]}
    """
    matched_rules = []
    failed_rules = []

    for rule in rules:
        field_name = rule["field_name"]
        op_symbol = rule["operator"]
        expected_raw = rule["expected_value"]
        user_raw = profile_data.get(field_name)

        rule_info = {
            "field_name": field_name,
            "operator": op_symbol,
            "expected_value": expected_raw,
            "your_value": user_raw,
        }

        if user_raw is None:
            failed_rules.append(
                {**rule_info, "reason": f"Your profile is missing a value for '{field_name}'"}
            )
            continue

        comparison_function = OPERATORS.get(op_symbol)
        if comparison_function is None:
            failed_rules.append(
                {**rule_info, "reason": f"Unsupported operator '{op_symbol}'"}
            )
            continue

        user_value = _coerce(user_raw)
        expected_value = _coerce(expected_raw)

        try:
            passed = comparison_function(user_value, expected_value)
        except TypeError:
            # e.g. trying ">=" between a number and a piece of text
            passed = False

        if passed:
            matched_rules.append(rule_info)
        else:
            failed_rules.append(
                {
                    **rule_info,
                    "reason": (
                        f"Your {field_name} ({user_raw}) does not satisfy "
                        f"the requirement: {field_name} {op_symbol} {expected_raw}"
                    ),
                }
            )

    eligible = len(failed_rules) == 0

    return {
        "eligible": eligible,
        "matched_rules": matched_rules,
        "failed_rules": failed_rules,
    }