import pandas as pd
import json
from collections import Counter


def datasource_utilization_count(evaluation_result):

    required_cols = {"verified", "rule_assignment"}

    missing_cols = required_cols - set(evaluation_result.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    verified_result = evaluation_result[evaluation_result["verified"] == True]

    ds_counter = Counter()

    for val in verified_result["rule_assignment"].dropna():
        if isinstance(val, str):
            try:
                assignment = json.loads(val)
            except json.JSONDecodeError:
                continue
        elif isinstance(val, dict):
            assignment = val
        else:
            continue

        ds_counter.update(assignment.values())

    return ds_counter


def counter_to_dataframe(counter):

    if not counter:
        return pd.DataFrame(columns=["datasource", "usage_count"])

    df = pd.DataFrame(
        counter.items(),
        columns=["datasource", "usage_count"]
    )

    return df.sort_values("usage_count", ascending=False)