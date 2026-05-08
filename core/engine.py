from pathlib import Path
import pandas as pd
import numpy as np
import core.models as models


BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR.parent / "data" / "kyc_data.csv"

try:
    df = pd.read_csv(DATA_PATH)
except FileNotFoundError:
    print("Error: kyc_data.csv not found.")
    exit(1)

full_match_field = [ 'firstinitial', 'firstname', 'middlename',
       'lastname', 'dayofbirth', 'monthofbirth', 'yearofbirth', 'streetname',
       'streetnumber', 'streettype', 'city', 'region', 'postalcode',
       'unitnumber', 'address1', 'taxid', 'socialinsurancenumber', 'voterid',
       'gender']

required_columns = set(["recordid", "datasource", "trumatch_confidence"])

def data_cleaning(df):
    
    df.drop_duplicates(inplace=True)
    df.fillna('unknown', inplace=True)
    return df



def data_validation(df):
    if df.empty:
        raise ValueError("Input data is empty.")
    
    if df["recordid"].isnull().any():
        raise ValueError("Null values found in 'recordid' column.")
    
    if df["datasource"].isnull().any():
        raise ValueError("Null values found in 'datasource' column.")
    
    valid_match_states = set(state.value for state in models.MatchFieldState)
    match_states = set(df[full_match_field].values.flatten())

    invalid_states = match_states - valid_match_states
    print(invalid_states)
    # if invalid_states:
    #     raise ValueError(f"Invalid match states found: {invalid_states}")
    


def field_validation(df):

    missing_columns = required_columns - set(df.columns)
    current_match_fields = set(df.columns) - required_columns

    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    if not current_match_fields.issubset(set(full_match_field)):
        raise ValueError(f"Invalid match fields: {current_match_fields - full_match_field}")



def build_datasource_result(df, datasource_id):
    
    match_fields = [col for col in df.columns if col not in required_columns]
    
    fields = {}
    row = df[df["datasource"] == datasource_id]

    for col in match_fields:
        fields[col] = models.MatchFieldState(row[col].values[0])
    
    confidence_score = row["trumatch_confidence"].values[0]

    output = models.DataSourceResult(
        datasource_id=datasource_id,
        fields=fields,
        confidence=confidence_score
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


def build_records(df):
    
    df = data_cleaning(df)

    data_validation(df)

    field_validation(df)
    
    # record = []

    # for rid in df["recordid"].unique():
    #     try: 
    #         record.append(build_record(df, rid))
    #     except Exception as e:
    #         print(f"Error processing record {rid}: {e}")
    
    # return record
    


print("Building records from input data...")
records = build_records(df)
if records:
    print(f"Successfully built {len(records)} records.")
    



