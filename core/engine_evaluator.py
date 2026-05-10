import core.models as Models


def evaluate_rule(rule, datasource_result):

    if "field" in rule:
        field = rule["field"]
        check = rule["check"]

        state = datasource_result.fields.get(
            field,
            Models.MatchFieldState.MISSING
        )

        if check == "match":
            return state == Models.MatchFieldState.MATCH

        if check == "not_nomatch":
            return state != Models.MatchFieldState.NOMATCH

        raise ValueError(f"Unknown check type: {check}")


    op = rule["op"]
    conditions = rule["conditions"]

    if op == "AND":
        return all(evaluate_rule(child, datasource_result) for child in conditions)

    if op == "OR":
        return any(evaluate_rule(child, datasource_result) for child in conditions)

    raise ValueError(f"Unknown operator: {op}")


def source_assignment(
        rule_index, rule_names,
        rule_results, 
        used_ds, rule_assignment
    ):

    if rule_index == len(rule_names):
        return True

    rule_name = rule_names[rule_index]
    candidate_datasources = rule_results.get(rule_name, [])

    for datasource_id in candidate_datasources:
        if datasource_id not in used_ds:
            rule_assignment[rule_name] = datasource_id
            used_ds.add(datasource_id)

            if source_assignment(
                    rule_index + 1, rule_names,
                    rule_results,
                    used_ds, rule_assignment
                ):
                return True

            used_ds.remove(datasource_id)
            del rule_assignment[rule_name]

    return False




def find_valid_source_assignment(rule_names, rule_results):

    used_ds = set()
    rule_assignment = {}

    verified = source_assignment(
        rule_index=0,
        rule_names=rule_names,
        rule_results=rule_results,
        used_ds=used_ds,
        rule_assignment=rule_assignment
    )

    return verified, rule_assignment


def evaluate_record(record, rules):

    rule_results = {}

    for rule in rules:
        rule_name = rule["name"]
        passing_datasources = []

        for datasource_id, datasource_result in record.datasources.items():
            if evaluate_rule(rule, datasource_result):
                passing_datasources.append(datasource_id)

        rule_results[rule_name] = passing_datasources

    rule_names = [rule["name"] for rule in rules]

    verified, rule_assignment = find_valid_source_assignment(
        rule_names=rule_names,
        rule_results=rule_results
    )


    output = {
        "record_id": record.record_id,
        "verified": verified,
        "rule_results": rule_results,
        "rule_assignment": rule_assignment,
    }

    return output

def evaluate_records(records, rules, limit=None):

    selected_records = records if limit is None else records[:limit]

    outputs = []

    for record in selected_records:
        outputs.append(evaluate_record(record, rules))

    return outputs