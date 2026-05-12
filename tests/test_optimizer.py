import pandas as pd
import pytest

import core.engine_optimizer as optimizer


def make_optimizer_df():
    return pd.DataFrame([
        {
            "record_id": 101,
            "verified": True,
            "rule_results": str({
                "rule_1": ["a", "b"],
                "rule_2": ["b", "c"],
            }),
        },
        {
            "record_id": 102,
            "verified": True,
            "rule_results": str({
                "rule_1": ["a"],
                "rule_2": ["c"],
            }),
        },
    ])


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
    assert set(result["verified_record_ids"]) == {101, 102}


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
            "record_id": 101,
            "verified": True,
            "rule_results": str({
                "rule_1": ["a"],
                "rule_2": ["b"],
            }),
        },
        {
            "record_id": 102,
            "verified": False,
            "rule_results": str({
                "rule_1": ["x"],
                "rule_2": ["y"],
            }),
        },
    ])

    source_cost = {
        "a": 1,
        "b": 2,
        "x": 100,
        "y": 100,
    }

    result = optimizer.solve_source_selection_pulp(
        df,
        source_cost,
        min_verify_rate=1.0,
    )

    assert result["status"] == "Optimal"
    assert result["actual_verified"] == 1
    assert result["verified_record_ids"] == [101]
    assert "x" not in result["selected_sources"]
    assert "y" not in result["selected_sources"]


def test_solver_returns_no_solution_when_no_valid_source_available():
    df = pd.DataFrame([
        {
            "record_id": 101,
            "verified": True,
            "rule_results": str({
                "rule_1": ["a"],
                "rule_2": ["b"],
            }),
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
            "record_id": 101,
            "rule_results": str({"rule_1": ["a"]}),
        }
    ])

    source_cost = {"a": 1}

    with pytest.raises(ValueError, match="Missing required columns"):
        optimizer.solve_source_selection_pulp(df, source_cost)


def test_solver_raises_for_missing_rule_results_column():
    df = pd.DataFrame([
        {
            "record_id": 101,
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
            "record_id": 101,
            "verified": True,
            "rule_results": str({
                "rule_1": ["a", "b"],
                "rule_2": ["a", "b"],
            }),
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

    assignment = result["assignments"][101]

    assert result["status"] == "Optimal"
    assert assignment["rule_1"] != assignment["rule_2"]