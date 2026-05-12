import pandas as pd
import pytest

import core.models as models
import core.engine_processor as processor


def make_valid_df():
    return pd.DataFrame([
        {
            "recordid": 101,
            "datasource": "a",
            "trumatch_confidence": 0.95,
            "firstname": "match",
            "lastname": "match",
            "dayofbirth": "missing",
        },
        {
            "recordid": 101,
            "datasource": "b",
            "trumatch_confidence": 0.80,
            "firstname": "nomatch",
            "lastname": "match",
            "dayofbirth": "unknown",
        },
        {
            "recordid": 102,
            "datasource": "a",
            "trumatch_confidence": 0.70,
            "firstname": "match",
            "lastname": "nomatch",
            "dayofbirth": "match",
        },
    ])


def test_full_match_fields_come_from_enum():
    assert "firstname" in processor.FULL_MATCH_FIELDS
    assert "lastname" in processor.FULL_MATCH_FIELDS
    assert "taxid" in processor.FULL_MATCH_FIELDS


def test_required_columns_come_from_enum():
    assert processor.REQUIRED_COLUMNS == [
        "recordid",
        "datasource",
        "trumatch_confidence",
    ]


def test_data_cleaning_standardizes_columns_and_values():
    df = pd.DataFrame([
        {
            " RecordID ": 101,
            " DataSource ": " A ",
            " Trumatch_Confidence ": 0.95,
            " FirstName ": " MATCH ",
            " LastName ": None,
        }
    ])

    cleaned = processor.data_cleaning(df)

    assert "recordid" in cleaned.columns
    assert "datasource" in cleaned.columns
    assert "trumatch_confidence" in cleaned.columns
    assert "firstname" in cleaned.columns
    assert "lastname" in cleaned.columns

    assert cleaned.loc[0, "firstname"] == "match"
    assert cleaned.loc[0, "lastname"] == "unknown"


def test_data_cleaning_drops_duplicates():
    df = pd.DataFrame([
        {
            "recordid": 101,
            "datasource": "a",
            "trumatch_confidence": 0.95,
            "firstname": "match",
        },
        {
            "recordid": 101,
            "datasource": "a",
            "trumatch_confidence": 0.95,
            "firstname": "match",
        },
    ])

    cleaned = processor.data_cleaning(df)

    assert len(cleaned) == 1


def test_field_validation_passes_valid_df():
    df = make_valid_df()

    processor.field_validation(df)


def test_field_validation_raises_for_missing_required_column():
    df = make_valid_df().drop(columns=["datasource"])

    with pytest.raises(ValueError, match="Missing required columns"):
        processor.field_validation(df)


def test_field_validation_raises_for_invalid_match_field():
    df = make_valid_df()
    df["invalid_kyc_field"] = "match"

    with pytest.raises(ValueError, match="Invalid match fields"):
        processor.field_validation(df)


def test_find_invalid_match_states_returns_invalid_states():
    df = make_valid_df()
    df.loc[0, "firstname"] = "bad_state"

    invalid_states = processor.find_invalid_match_states(df)

    assert invalid_states == {"bad_state"}


def test_find_invalid_match_states_returns_empty_set_for_valid_df():
    df = make_valid_df()

    invalid_states = processor.find_invalid_match_states(df)

    assert invalid_states == set()


def test_get_rows_with_invalid_states_returns_only_bad_rows():
    df = make_valid_df()
    df.loc[1, "firstname"] = "bad_state"

    rows = processor.get_rows_with_invalid_states(df, {"bad_state"})

    assert len(rows) == 1
    assert rows.iloc[0]["datasource"] == "b"


def test_replace_invalid_states_replaces_values():
    df = make_valid_df()
    df.loc[0, "firstname"] = "bad_state"

    fixed = processor.replace_invalid_states(df, {"bad_state": "unknown"})

    assert fixed.loc[0, "firstname"] == "unknown"


def test_data_validation_raises_for_empty_df():
    df = pd.DataFrame()

    with pytest.raises(ValueError, match="Input data is empty"):
        processor.data_validation(df)


def test_data_validation_raises_for_invalid_match_state():
    df = make_valid_df()
    df.loc[0, "firstname"] = "bad_state"

    with pytest.raises(ValueError, match="Invalid match states still exist"):
        processor.data_validation(df)


def test_data_validation_passes_valid_df():
    df = make_valid_df()

    processor.data_validation(df)


def test_build_datasource_result_returns_datasource_object():
    df = make_valid_df()

    result = processor.build_datasource_result(df, "a")

    assert isinstance(result, models.DataSourceResult)
    assert result.datasource_id == "a"
    assert result.confidence == 0.95
    assert result.fields["firstname"] == models.MatchFieldState.MATCH
    assert result.fields["lastname"] == models.MatchFieldState.MATCH


def test_build_record_returns_record_entry():
    df = make_valid_df()

    record = processor.build_record(df, 101)

    assert isinstance(record, models.RecordEntry)
    assert record.record_id == 101
    assert set(record.datasources.keys()) == {"a", "b"}


def test_build_records_returns_all_records():
    df = make_valid_df()

    records = processor.build_records(df)

    assert len(records) == 2
    assert records[0].record_id == 101
    assert records[1].record_id == 102