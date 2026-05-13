import math
import pulp
import ast
import pandas as pd 

# Convert rule_results into a dictionary format
def normalize_rule_results(value):
    if isinstance(value, dict):
        return value

    if isinstance(value, str):
        return ast.literal_eval(value)

    raise ValueError(f"Invalid rule_results value: {value}")

# Get all datasources that appear in rule results
def get_available_sources(evaluation_df):
    sources = set()

    for value in evaluation_df["rule_results"]:
        rule_results = normalize_rule_results(value)

        for datasource_list in rule_results.values():
            sources.update(datasource_list)

    return sorted(sources)

# Optimize datasource selection while meeting the target verification rate
def solve_source_selection_pulp(df, source_cost, min_verify_rate=1.0, time_limit_sec=60):


    required_cols = {"verified", "rule_results"}

    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    df = df[df["verified"] == True].copy()
    
    # df['rule_results'] = df['rule_results'].apply(ast.literal_eval)
    df = df.reset_index(drop=True).copy()

    sources = sorted(source_cost.keys())
    n_records = len(df)

    required_verified = math.ceil(min_verify_rate * n_records)
    model = pulp.LpProblem("source_selection", pulp.LpMinimize)


    # Data source selection variables
    x = {d: pulp.LpVariable(f"select_{d}", cat="Binary") for d in sources}

    # Record verification variables
    z = {r: pulp.LpVariable(f"record_{r}_verified", cat="Binary") for r in range(n_records)}

    # Rule assignment variables: y[(r, rule, d)] = 1 if record r's rule is satisfied by data source d
    y = {}


    for r in range(n_records):

        record_rules = df.loc[r, "rule_results"]
        rules = list(record_rules.keys())

        for rule in rules:
            valid_candidates = [d for d in record_rules[rule] if d in source_cost]
            rule_assignments = []

            for d in valid_candidates:
                assign_var = pulp.LpVariable(f"assign_r{r}_{rule}_{d}", cat="Binary")
                y[(r, rule, d)] = assign_var
                rule_assignments.append(assign_var)

                model += assign_var <= x[d]

            model += (pulp.lpSum(rule_assignments)== z[r])

        for d in sources:
            assignments_using_d = [y[(r, rule, d)] for rule in rules if (r, rule, d) in y]
            if assignments_using_d:
                model += ( pulp.lpSum(assignments_using_d) <= 1)

    # Enforce minimum verification target
    model += (pulp.lpSum(z[r] for r in range(n_records)) >= required_verified)

    # Minimize selected datasource cost
    model += pulp.lpSum(source_cost[d] * x[d] for d in sources)

    solver = pulp.PULP_CBC_CMD(timeLimit=time_limit_sec,msg=False)

    status_code = model.solve(solver)
    status = pulp.LpStatus[status_code]

    if status != "Optimal":

        return {
            "status": "NO_SOLUTION",
            "solver_status": status,
            "min_verify_rate": min_verify_rate,
        }


    selected_sources = [d for d in sources if pulp.value(x[d]) > 0.5]
    verified_rows = [r for r in range(n_records) if pulp.value(z[r]) > 0.5]
    unverified_rows = [r for r in range(n_records) if pulp.value(z[r]) < 0.5]
    verified_record_ids = (df.loc[verified_rows, "record_id"].tolist())
    unverified_record_ids = (df.loc[unverified_rows, "record_id"].tolist())

    assignments = {}

    for r in verified_rows:

        record_id = df.loc[r, "record_id"]
        record_rules = df.loc[r, "rule_results"]
        assignments[record_id] = {}

        for rule in record_rules:
            for d in record_rules[rule]:
                if ((r, rule, d) in y and pulp.value(y[(r, rule, d)]) > 0.5):
                    assignments[record_id][rule] = d

    cost_per_record = sum(source_cost[d] for d in selected_sources)

    total_cost = cost_per_record * n_records

    output =  {
            "status": status,
            "min_verify_rate": min_verify_rate,
            "required_verified": required_verified,
            "actual_verified": len(verified_record_ids),
            "actual_verify_rate": (len(verified_record_ids) / n_records),
            "selected_sources": selected_sources,
            "cost_per_record": cost_per_record,
            "total_cost": total_cost,
            "verified_record_ids": verified_record_ids,
            "unverified_record_ids": unverified_record_ids,
            "assignments": assignments,
        }
    
    return output

# Convert optimized rule assignments into a dataframe
def optimized_assignment_df_builder(optimized_output):
    assignments = optimized_output['assignments']
    df =  pd.DataFrame(assignments)
    df = df.transpose()
    return df