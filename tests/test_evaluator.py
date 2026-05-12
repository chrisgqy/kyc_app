import pytest

import core.models as Models
import core.engine_evaluator as evaluator


def make_datasource_result(datasource_id="a"):
    return Models.DataSourceResult(
        datasource_id=datasource_id,
        confidence=0.95,
        fields={
            "firstname": Models.MatchFieldState.MATCH,
            "lastname": Models.MatchFieldState.NOMATCH,
            "taxid": Models.MatchFieldState.MISSING,
            "gender": Models.MatchFieldState.UNKNOWN,
        },
    )


def make_record():
    return Models.RecordEntry(
        record_id=101,
        datasources={
            "a": Models.DataSourceResult(
                datasource_id="a",
                confidence=0.95,
                fields={
                    "firstname": Models.MatchFieldState.MATCH,
                    "lastname": Models.MatchFieldState.MATCH,
                    "taxid": Models.MatchFieldState.MISSING,
                },
            ),
            "b": Models.DataSourceResult(
                datasource_id="b",
                confidence=0.80,
                fields={
                    "firstname": Models.MatchFieldState.NOMATCH,
                    "lastname": Models.MatchFieldState.MATCH,
                    "taxid": Models.MatchFieldState.MATCH,
                },
            ),
            "c": Models.DataSourceResult(
                datasource_id="c",
                confidence=0.70,
                fields={
                    "firstname": Models.MatchFieldState.MATCH,
                    "lastname": Models.MatchFieldState.NOMATCH,
                    "taxid": Models.MatchFieldState.MATCH,
                },
            ),
        },
    )


def test_evaluate_check_match():
    assert evaluator.evaluate_check(
        Models.MatchFieldState.MATCH,
        Models.MatchCheck.MATCH,
    ) is True

    assert evaluator.evaluate_check(
        Models.MatchFieldState.NOMATCH,
        Models.MatchCheck.MATCH,
    ) is False


def test_evaluate_check_nomatch():
    assert evaluator.evaluate_check(
        Models.MatchFieldState.NOMATCH,
        Models.MatchCheck.NOMATCH,
    ) is True

    assert evaluator.evaluate_check(
        Models.MatchFieldState.MATCH,
        Models.MatchCheck.NOMATCH,
    ) is False


def test_evaluate_check_missing():
    assert evaluator.evaluate_check(
        Models.MatchFieldState.MISSING,
        Models.MatchCheck.MISSING,
    ) is True


def test_evaluate_check_unknown():
    assert evaluator.evaluate_check(
        Models.MatchFieldState.UNKNOWN,
        Models.MatchCheck.UNKNOWN,
    ) is True


def test_evaluate_check_not_match():
    assert evaluator.evaluate_check(
        Models.MatchFieldState.NOMATCH,
        Models.MatchCheck.NOT_MATCH,
    ) is True

    assert evaluator.evaluate_check(
        Models.MatchFieldState.MATCH,
        Models.MatchCheck.NOT_MATCH,
    ) is False


def test_evaluate_check_not_nomatch():
    assert evaluator.evaluate_check(
        Models.MatchFieldState.MATCH,
        Models.MatchCheck.NOT_NOMATCH,
    ) is True

    assert evaluator.evaluate_check(
        Models.MatchFieldState.NOMATCH,
        Models.MatchCheck.NOT_NOMATCH,
    ) is False


def test_evaluate_check_not_missing():
    assert evaluator.evaluate_check(
        Models.MatchFieldState.MATCH,
        Models.MatchCheck.NOT_MISSING,
    ) is True

    assert evaluator.evaluate_check(
        Models.MatchFieldState.MISSING,
        Models.MatchCheck.NOT_MISSING,
    ) is False


def test_evaluate_check_not_unknown():
    assert evaluator.evaluate_check(
        Models.MatchFieldState.MATCH,
        Models.MatchCheck.NOT_UNKNOWN,
    ) is True

    assert evaluator.evaluate_check(
        Models.MatchFieldState.UNKNOWN,
        Models.MatchCheck.NOT_UNKNOWN,
    ) is False


def test_evaluate_check_raises_for_unknown_check():
    with pytest.raises(ValueError, match="Unknown check type"):
        evaluator.evaluate_check(
            Models.MatchFieldState.MATCH,
            "bad_check",
        )


def test_evaluate_rule_single_field_match():
    datasource = make_datasource_result()

    rule = {
        "field": "firstname",
        "check": Models.MatchCheck.MATCH,
    }

    assert evaluator.evaluate_rule(rule, datasource) is True


def test_evaluate_rule_missing_field_defaults_to_missing():
    datasource = make_datasource_result()

    rule = {
        "field": "not_existing_field",
        "check": Models.MatchCheck.MISSING,
    }

    assert evaluator.evaluate_rule(rule, datasource) is True


def test_evaluate_rule_and_passes():
    datasource = make_datasource_result()

    rule = {
        "op": "AND",
        "conditions": [
            {"field": "firstname", "check": Models.MatchCheck.MATCH},
            {"field": "lastname", "check": Models.MatchCheck.NOMATCH},
        ],
    }

    assert evaluator.evaluate_rule(rule, datasource) is True


def test_evaluate_rule_and_fails():
    datasource = make_datasource_result()

    rule = {
        "op": "AND",
        "conditions": [
            {"field": "firstname", "check": Models.MatchCheck.MATCH},
            {"field": "lastname", "check": Models.MatchCheck.MATCH},
        ],
    }

    assert evaluator.evaluate_rule(rule, datasource) is False


def test_evaluate_rule_or_passes():
    datasource = make_datasource_result()

    rule = {
        "op": "OR",
        "conditions": [
            {"field": "firstname", "check": Models.MatchCheck.NOMATCH},
            {"field": "lastname", "check": Models.MatchCheck.NOMATCH},
        ],
    }

    assert evaluator.evaluate_rule(rule, datasource) is True


def test_evaluate_rule_or_fails():
    datasource = make_datasource_result()

    rule = {
        "op": "OR",
        "conditions": [
            {"field": "firstname", "check": Models.MatchCheck.NOMATCH},
            {"field": "lastname", "check": Models.MatchCheck.MATCH},
        ],
    }

    assert evaluator.evaluate_rule(rule, datasource) is False


def test_evaluate_rule_nested_conditions():
    datasource = make_datasource_result()

    rule = {
        "op": "AND",
        "conditions": [
            {
                "op": "OR",
                "conditions": [
                    {"field": "firstname", "check": Models.MatchCheck.MATCH},
                    {"field": "lastname", "check": Models.MatchCheck.MATCH},
                ],
            },
            {"field": "taxid", "check": Models.MatchCheck.MISSING},
        ],
    }

    assert evaluator.evaluate_rule(rule, datasource) is True


def test_evaluate_rule_raises_for_unknown_operator():
    datasource = make_datasource_result()

    rule = {
        "op": "BAD_OPERATOR",
        "conditions": [],
    }

    with pytest.raises(ValueError, match="Unknown operator"):
        evaluator.evaluate_rule(rule, datasource)


def test_find_valid_source_assignment_success():
    rule_names = ["rule_1", "rule_2"]

    rule_results = {
        "rule_1": ["a", "b"],
        "rule_2": ["b", "c"],
    }

    verified, assignment = evaluator.find_valid_source_assignment(
        rule_names,
        rule_results,
    )

    assert verified is True
    assert assignment["rule_1"] != assignment["rule_2"]
    assert set(assignment.keys()) == {"rule_1", "rule_2"}


def test_find_valid_source_assignment_fails_when_same_only_source():
    rule_names = ["rule_1", "rule_2"]

    rule_results = {
        "rule_1": ["a"],
        "rule_2": ["a"],
    }

    verified, assignment = evaluator.find_valid_source_assignment(
        rule_names,
        rule_results,
    )

    assert verified is False
    assert assignment == {}


def test_find_valid_source_assignment_fails_when_rule_has_no_candidates():
    rule_names = ["rule_1", "rule_2"]

    rule_results = {
        "rule_1": ["a"],
        "rule_2": [],
    }

    verified, assignment = evaluator.find_valid_source_assignment(
        rule_names,
        rule_results,
    )

    assert verified is False
    assert assignment == {}


def test_evaluate_record_verified_true():
    record = make_record()

    rules = [
        {
            "name": "rule_1",
            "field": "firstname",
            "check": Models.MatchCheck.MATCH,
        },
        {
            "name": "rule_2",
            "field": "taxid",
            "check": Models.MatchCheck.MATCH,
        },
    ]

    output = evaluator.evaluate_record(record, rules)

    assert output["record_id"] == 101
    assert output["verified"] is True
    assert output["rule_results"] == {
        "rule_1": ["a", "c"],
        "rule_2": ["b", "c"],
    }
    assert output["rule_assignment"]["rule_1"] != output["rule_assignment"]["rule_2"]


def test_evaluate_record_verified_false_due_to_same_source_constraint():
    record = make_record()

    rules = [
        {
            "name": "rule_1",
            "field": "firstname",
            "check": Models.MatchCheck.NOMATCH,
        },
        {
            "name": "rule_2",
            "field": "firstname",
            "check": Models.MatchCheck.NOMATCH,
        },
    ]

    output = evaluator.evaluate_record(record, rules)

    assert output["record_id"] == 101
    assert output["verified"] is False
    assert output["rule_results"] == {
        "rule_1": ["b"],
        "rule_2": ["b"],
    }
    assert output["rule_assignment"] == {}


def test_evaluate_records_all_records():
    records = [make_record(), make_record()]

    rules = [
        {
            "name": "rule_1",
            "field": "firstname",
            "check": Models.MatchCheck.MATCH,
        }
    ]

    outputs = evaluator.evaluate_records(records, rules)

    assert len(outputs) == 2
    assert outputs[0]["record_id"] == 101


def test_evaluate_records_with_limit():
    records = [make_record(), make_record(), make_record()]

    rules = [
        {
            "name": "rule_1",
            "field": "firstname",
            "check": Models.MatchCheck.MATCH,
        }
    ]

    outputs = evaluator.evaluate_records(records, rules, limit=2)

    assert len(outputs) == 2