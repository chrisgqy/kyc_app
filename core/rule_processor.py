import re
import core.models as Models

# Split raw rule text into parser-friendly tokens
def tokenize_rule(rule_text):

    rule_text = rule_text.lower().strip()

    tokens = re.findall(
        r"\(|\)|and|or|notnomatch|[a-zA-Z0-9_]+",rule_text)

    return tokens

# Parse one rule string into a rule tree
def parse_rule(rule_text, rule_name):

    tokens = tokenize_rule(rule_text)

    if not tokens:
        raise ValueError("Rule is empty.")
    rule_tree, next_index = parse_expression(tokens, 0)

    if next_index != len(tokens):
        raise ValueError(f"Unexpected token: {tokens[next_index]}")

    rule_tree = {
        "name": rule_name, **rule_tree
    }

    return rule_tree


# Parse AND / OR expressions
def parse_expression(tokens, index):

    current, index = parse_term(tokens, index)

    allowed_ops = {op.value.lower() for op in Models.LogicalOperator}

    while index < len(tokens) and tokens[index] in allowed_ops:
        op = tokens[index].upper()
        index += 1

        next_condition, index = parse_term(tokens, index)

        if isinstance(current, dict) and current.get("op") == op:
            current["conditions"].append(next_condition)

        else:
            current = {"op": op,"conditions": [current, next_condition]}

    return current, index


# Parse one field condition or parenthesized expression
def parse_term(tokens, index):

    if index >= len(tokens):
        raise ValueError("Unexpected end of rule.")

    if tokens[index] == "(":
        index += 1

        expression, index = parse_expression(tokens, index)

        if index >= len(tokens) or tokens[index] != ")":
            raise ValueError("Missing closing parenthesis.")

        index += 1

        return expression, index

    # notnomatch field => field must not be NOMATCH
    if tokens[index] == "notnomatch":
        index += 1

        if index >= len(tokens):
            raise ValueError("Expected field after notnomatch.")

        field = tokens[index]
        index += 1

        return {
            "field": field,
            "check": "not_nomatch"
        }, index

    # Default field check is exact match
    field = tokens[index]
    index += 1

    output = {"field": field, "check": "match"}
    return output


def parse_rules(rule_texts):

    rules = []

    for i, rule_text in enumerate(rule_texts, start=1):
        rule = parse_rule(
            rule_text=rule_text,
            rule_name=f"rule_{i}"
        )

        rules.append(rule)

    return rules

# Parse multiple rule strings
def split_rule_input(raw_text):
    rule_texts = []

    for line in raw_text.splitlines():
        line = line.strip()

        if line and line not in rule_texts:
            rule_texts.append(line)

    return rule_texts