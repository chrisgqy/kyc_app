from pathlib import Path
import pandas as pd
import numpy as np
import core.models as models
import pickle


full_match_field = [field.value for field in models.FullMatchField]
required_columns = set([col.value for col in models.RequiredColumn])


def data_cleaning(df):
    
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower()
    df.drop_duplicates(inplace=True)
    df.fillna("unknown", inplace=True)

    for col in df.columns:
        if col not in required_columns:
            df[col] = df[col].astype(str).str.strip().str.lower()

    return df


def field_validation(df):
    
    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    
    current_match_fields = set(df.columns) - required_columns
    invalid_fields = current_match_fields - set(full_match_field)

    if invalid_fields:
        raise ValueError(f"Invalid match fields: {invalid_fields}")


def find_invalid_match_states(df):

    
    valid_match_states = set(state.value for state in models.MatchFieldState)
    
    match_fields =  [col for col in full_match_field if col in df.columns]
    matchded_states = set(df[match_fields].values.flatten())

    invalid_states = matchded_states - valid_match_states

    return invalid_states 


def get_rows_with_invalid_states(df, invalid_states):
   
    match_fields = [col for col in full_match_field if col in df.columns]
    mask = df[match_fields].isin(invalid_states).any(axis=1)
    df.sort_values(by='recordid', ascending = True, inplace = True)

    return df[mask]


def replace_invalid_states(df, replacements: dict):
    df = df.copy()
    return df.replace(replacements)


def data_validation(df):
    if df.empty:
        raise ValueError("Input data is empty.")
    
    invalid_states = find_invalid_match_states(df)

    if invalid_states:
        raise ValueError(f"Invalid match states still exist: {invalid_states}")


def build_datasource_result(df, datasource_id):
    
    match_fields = [col for col in df.columns if col not in required_columns]
    
    row = df[df["datasource"] == datasource_id].iloc[0]

    fields = {
        col: models.MatchFieldState(row[col])
        for col in match_fields
    }
    
    output = models.DataSourceResult(
        datasource_id=datasource_id,
        fields=fields,
        confidence=float(row["trumatch_confidence"])
    )

    return output 


def build_record(df, record_id):
    datasources = {}
    record = df[df["recordid"] == record_id]

    for ds in record["datasource"].unique():
        datasources[ds] = build_datasource_result(record, ds)
    
    output = models.RecordEntry(
        record_id=record_id,
        datasources=datasources
    )

    return output


def build_records(df):
    
    df = data_cleaning(df)
    data_validation(df)
    field_validation(df)
    
    record = []

    for rid in df["recordid"].unique():
        try: 
            record.append(build_record(df, rid))
        except Exception as e:
            print(f"Error processing record {rid}: {e}")

    return record


