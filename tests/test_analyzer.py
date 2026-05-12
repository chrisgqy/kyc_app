from collections import Counter
import json

import pandas as pd
import pytest

import core.engine_analyzer as analyzer


def test_datasource_utilization_count_with_dict_assignments():
    evaluation_result = pd.DataFrame([
        {
            "record_id": 101,
            "verified": True,
            "rule_assignment": {
                "rule_1": "a",
                "rule_2": "b",
            },
        },
        {
            "record_id": 102,
            "verified": True,
            "rule_assignment": {
                "rule_1": "a",
                "rule_2": "c",
            },
        },
    ])

    counter = analyzer.datasource_utilization_count(evaluation_result)

    assert counter == Counter({"a": 2, "b": 1, "c": 1})


def test_datasource_utilization_count_with_json_string_assignments():
    evaluation_result = pd.DataFrame([
        {
            "verified": True,
            "rule_assignment": json.dumps({
                "rule_1": "a",
                "rule_2": "b",
            }),
        },
        {
            "verified": True,
            "rule_assignment": json.dumps({
                "rule_1": "a",
                "rule_2": "c",
            }),
        },
    ])

    counter = analyzer.datasource_utilization_count(evaluation_result)

    assert counter == Counter({"a": 2, "b": 1, "c": 1})


def test_datasource_utilization_count_ignores_unverified_rows():
    evaluation_result = pd.DataFrame([
        {
            "verified": True,
            "rule_assignment": {"rule_1": "a"},
        },
        {
            "verified": False,
            "rule_assignment": {"rule_1": "b"},
        },
    ])

    counter = analyzer.datasource_utilization_count(evaluation_result)

    assert counter == Counter({"a": 1})


def test_datasource_utilization_count_ignores_invalid_json_string():
    evaluation_result = pd.DataFrame([
        {
            "verified": True,
            "rule_assignment": '{"rule_1": "a"}',
        },
        {
            "verified": True,
            "rule_assignment": "{bad json}",
        },
    ])

    counter = analyzer.datasource_utilization_count(evaluation_result)

    assert counter == Counter({"a": 1})


def test_datasource_utilization_count_ignores_none_and_invalid_types():
    evaluation_result = pd.DataFrame([
        {
            "verified": True,
            "rule_assignment": {"rule_1": "a"},
        },
        {
            "verified": True,
            "rule_assignment": None,
        },
        {
            "verified": True,
            "rule_assignment": ["not", "a", "dict"],
        },
    ])

    counter = analyzer.datasource_utilization_count(evaluation_result)

    assert counter == Counter({"a": 1})


def test_datasource_utilization_count_raises_for_missing_verified_column():
    evaluation_result = pd.DataFrame([
        {
            "rule_assignment": {"rule_1": "a"},
        }
    ])

    with pytest.raises(ValueError, match="Missing required columns"):
        analyzer.datasource_utilization_count(evaluation_result)


def test_datasource_utilization_count_raises_for_missing_rule_assignment_column():
    evaluation_result = pd.DataFrame([
        {
            "verified": True,
        }
    ])

    with pytest.raises(ValueError, match="Missing required columns"):
        analyzer.datasource_utilization_count(evaluation_result)


def test_counter_to_dataframe_with_values():
    counter = Counter({"a": 3, "b": 1, "c": 2})

    df = analyzer.counter_to_dataframe(counter)

    assert list(df.columns) == ["datasource", "usage_count"]
    assert list(df["datasource"]) == ["a", "c", "b"]
    assert list(df["usage_count"]) == [3, 2, 1]


def test_counter_to_dataframe_empty_counter():
    counter = Counter()

    df = analyzer.counter_to_dataframe(counter)

    assert list(df.columns) == ["datasource", "usage_count"]
    assert df.empty