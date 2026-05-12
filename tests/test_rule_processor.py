import pytest

import core.rule_processor as rule_processor


def test_tokenize_rule_lowercases_and_splits_tokens():
    rule_text = "(FirstName OR FirstInitial) AND notnomatch LastName"

    tokens = rule_processor.tokenize_rule(rule_text)

    assert tokens == [
        "(",
        "firstname",
        "or",
        "firstinitial",
        ")",
        "and",
        "notnomatch",
        "lastname",
    ]


def test_tokenize_rule_empty_string_returns_empty_list():
    assert rule_processor.tokenize_rule("") == []


def test_parse_simple_field_defaults_to_match():
    rule = rule_processor.parse_rule("firstname", "rule_1")

    assert rule == {
        "name": "rule_1",
        "field": "firstname",
        "check": "match",
    }


def test_parse_notnomatch_field():
    rule = rule_processor.parse_rule("notnomatch lastname", "rule_1")

    assert rule == {
        "name": "rule_1",
        "field": "lastname",
        "check": "not_nomatch",
    }


def test_parse_or_expression():
    rule = rule_processor.parse_rule(
        "firstname or firstinitial",
        "rule_1",
    )

    assert rule == {
        "name": "rule_1",
        "op": "OR",
        "conditions": [
            {"field": "firstname", "check": "match"},
            {"field": "firstinitial", "check": "match"},
        ],
    }


def test_parse_and_expression():
    rule = rule_processor.parse_rule(
        "firstname and lastname",
        "rule_1",
    )

    assert rule == {
        "name": "rule_1",
        "op": "AND",
        "conditions": [
            {"field": "firstname", "check": "match"},
            {"field": "lastname", "check": "match"},
        ],
    }


def test_parse_parentheses_expression():
    rule = rule_processor.parse_rule(
        "(firstname or firstinitial) and lastname",
        "rule_1",
    )

    assert rule == {
        "name": "rule_1",
        "op": "AND",
        "conditions": [
            {
                "op": "OR",
                "conditions": [
                    {"field": "firstname", "check": "match"},
                    {"field": "firstinitial", "check": "match"},
                ],
            },
            {"field": "lastname", "check": "match"},
        ],
    }


def test_parse_nested_expression():
    rule = rule_processor.parse_rule(
        "(firstname or firstinitial) and (city or postalcode)",
        "rule_1",
    )

    assert rule == {
        "name": "rule_1",
        "op": "AND",
        "conditions": [
            {
                "op": "OR",
                "conditions": [
                    {"field": "firstname", "check": "match"},
                    {"field": "firstinitial", "check": "match"},
                ],
            },
            {
                "op": "OR",
                "conditions": [
                    {"field": "city", "check": "match"},
                    {"field": "postalcode", "check": "match"},
                ],
            },
        ],
    }


def test_parse_multiple_same_operator_flattens_conditions():
    rule = rule_processor.parse_rule(
        "firstname and lastname and taxid",
        "rule_1",
    )

    assert rule == {
        "name": "rule_1",
        "op": "AND",
        "conditions": [
            {"field": "firstname", "check": "match"},
            {"field": "lastname", "check": "match"},
            {"field": "taxid", "check": "match"},
        ],
    }


def test_parse_empty_rule_raises_error():
    with pytest.raises(ValueError, match="Rule is empty"):
        rule_processor.parse_rule("", "rule_1")


def test_parse_missing_closing_parenthesis_raises_error():
    with pytest.raises(ValueError, match="Missing closing parenthesis"):
        rule_processor.parse_rule("(firstname or lastname", "rule_1")


def test_parse_notnomatch_without_field_raises_error():
    with pytest.raises(ValueError, match="Expected field after notnomatch"):
        rule_processor.parse_rule("notnomatch", "rule_1")


def test_parse_unexpected_extra_token_raises_error():
    with pytest.raises(ValueError, match="Unexpected token"):
        rule_processor.parse_rule("firstname )", "rule_1")


def test_parse_rules_assigns_rule_names():
    rule_texts = [
        "firstname",
        "lastname",
    ]

    rules = rule_processor.parse_rules(rule_texts)

    assert rules[0]["name"] == "rule_1"
    assert rules[1]["name"] == "rule_2"
    assert rules[0]["field"] == "firstname"
    assert rules[1]["field"] == "lastname"


def test_split_rule_input_removes_blank_lines_and_duplicates():
    raw_text = """
    firstname and lastname

    firstname and lastname
    taxid
    """

    rule_texts = rule_processor.split_rule_input(raw_text)

    assert rule_texts == [
        "firstname and lastname",
        "taxid",
    ]