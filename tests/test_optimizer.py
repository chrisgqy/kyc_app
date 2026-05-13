import pandas as pd
import pytest

import core.engine_optimizer as optimizer


def make_optimizer_df():
    return pd.DataFrame([
        {
            "record_id": "record_1",
            "verified": True,
            "rule_results": {
                "rule_1": ["a", "b"],
                "rule_2": ["b", "c"],
            },
        },
        {
            "record_id": "record_2",
            "verified": True,
            "rule_results": {
                "rule_1": ["a"],
                "rule_2": ["c"],
            },
        },
    ])


def test_normalize_rule_results_accepts_dict():
    value = {"rule_1": ["a", "b"]}

    result = optimizer.normalize_rule_results(value)

    assert result == {"rule_1": ["a", "b"]}


def test_normalize_rule_results_accepts_string_dict():
    value = "{'rule_1': ['a', 'b']}"

    result = optimizer.normalize_rule_results(value)

    assert result == {"rule_1": ["a", "b"]}


def test_normalize_rule_results_rejects_invalid_type():
    with pytest.raises(ValueError, match="Invalid rule_results value"):
        optimizer.normalize_rule_results(123)


def test_get_available_sources_from_dict_values():
    df = pd.DataFrame([
        {
            "rule_results": {
                "rule_1": ["b", "c"],
                "rule_2": ["b", "c", "f", "g"],
            }
        }
    ])

    sources = optimizer.get_available_sources(df)

    assert sources == ["b", "c", "f", "g"]


def test_get_available_sources_from_string_values():
    df = pd.DataFrame([
        {
            "rule_results": "{'rule_1': ['b', 'c'], 'rule_2': ['f', 'g']}"
        }
    ])

    sources = optimizer.get_available_sources(df)

    assert sources == ["b", "c", "f", "g"]


def test_solver_returns_optimal_solution():
    df = make_optimizer_df()

    source_cost = {
        "a": 1,
        "b": 10,
        "c": 2,
    }

    result = optimizer.solve_source_selection_pulp(
        df,
        source_cost,
        min_verify_rate=1.0,
    )

    assert result["status"] == "Optimal"
    assert result["actual_verified"] == 2
    assert result["actual_verify_rate"] == 1.0
    assert set(result["selected_sources"]) == {"a", "c"}
    assert result["cost_per_record"] == 3
    assert result["total_cost"] == 6
    assert set(result["verified_record_ids"]) == {"record_1", "record_2"}


def test_solver_respects_min_verify_rate_partial():
    df = make_optimizer_df()

    source_cost = {
        "a": 1,
        "b": 10,
        "c": 2,
    }

    result = optimizer.solve_source_selection_pulp(
        df,
        source_cost,
        min_verify_rate=0.5,
    )

    assert result["status"] == "Optimal"
    assert result["required_verified"] == 1
    assert result["actual_verified"] >= 1


def test_solver_filters_unverified_input_rows():
    df = pd.DataFrame([
        {
            "record_id": "record_1",
            "verified": True,
            "rule_results": {
                "rule_1": ["a"],
                "rule_2": ["b"],
            },
        },
        {
            "record_id": "record_2",
            "verified": False,
            "rule_results": {
                "rule_1": ["x"],
                "rule_2": ["y"],
            },
        },
    ])

    source_cost = {
        "a": 1,
        "b": 2,
    }

    result = optimizer.solve_source_selection_pulp(
        df,
        source_cost,
        min_verify_rate=1.0,
    )

    assert result["status"] == "Optimal"
    assert result["actual_verified"] == 1
    assert result["verified_record_ids"] == ["record_1"]
    assert set(result["selected_sources"]) == {"a", "b"}


def test_solver_returns_no_solution_when_rule_has_no_valid_source():
    df = pd.DataFrame([
        {
            "record_id": "record_1",
            "verified": True,
            "rule_results": {
                "rule_1": ["a"],
                "rule_2": ["b"],
            },
        },
    ])

    source_cost = {
        "a": 1,
    }

    result = optimizer.solve_source_selection_pulp(
        df,
        source_cost,
        min_verify_rate=1.0,
    )

    assert result["status"] == "NO_SOLUTION"
    assert result["solver_status"] != "Optimal"


def test_solver_raises_for_missing_verified_column():
    df = pd.DataFrame([
        {
            "record_id": "record_1",
            "rule_results": {
                "rule_1": ["a"],
            },
        }
    ])

    source_cost = {"a": 1}

    with pytest.raises(ValueError, match="Missing required columns"):
        optimizer.solve_source_selection_pulp(df, source_cost)


def test_solver_raises_for_missing_rule_results_column():
    df = pd.DataFrame([
        {
            "record_id": "record_1",
            "verified": True,
        }
    ])

    source_cost = {"a": 1}

    with pytest.raises(ValueError, match="Missing required columns"):
        optimizer.solve_source_selection_pulp(df, source_cost)


def test_solver_assignments_use_selected_sources():
    df = make_optimizer_df()

    source_cost = {
        "a": 1,
        "b": 10,
        "c": 2,
    }

    result = optimizer.solve_source_selection_pulp(
        df,
        source_cost,
        min_verify_rate=1.0,
    )

    selected_sources = set(result["selected_sources"])

    for record_assignment in result["assignments"].values():
        for datasource in record_assignment.values():
            assert datasource in selected_sources


def test_solver_does_not_reuse_same_datasource_for_two_rules_in_same_record():
    df = pd.DataFrame([
        {
            "record_id": "record_1",
            "verified": True,
            "rule_results": {
                "rule_1": ["a", "b"],
                "rule_2": ["a", "b"],
            },
        },
    ])

    source_cost = {
        "a": 1,
        "b": 2,
    }

    result = optimizer.solve_source_selection_pulp(
        df,
        source_cost,
        min_verify_rate=1.0,
    )

    assignment = result["assignments"]["record_1"]

    assert result["status"] == "Optimal"
    assert assignment["rule_1"] != assignment["rule_2"]


def test_optimized_assignment_df_builder():
    optimized_output = {
        "assignments": {
            "record_1": {
                "rule_1": "a",
                "rule_2": "c",
            },
            "record_2": {
                "rule_1": "a",
                "rule_2": "c",
            },
        }
    }

    df = optimizer.optimized_assignment_df_builder(optimized_output)

    assert list(df.index) == ["record_1", "record_2"]
    assert list(df.columns) == ["rule_1", "rule_2"]
    assert df.loc["record_1", "rule_1"] == "a"