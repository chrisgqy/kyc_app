import pickle
import json
from io import BytesIO

import pandas as pd
import streamlit as st

import core.models as Models
import core.engine_processor as EP
import core.rule_processor as RP
import core.engine_evaluator as EA



st.set_page_config(
    page_title="KYC App",
    layout="wide"
)

st.markdown("""
<style>

/* Sidebar page navigation */
[data-testid="stSidebarNav"] {
    font-size: 24px;
}

/* Individual page buttons */
[data-testid="stSidebarNav"] span {
    font-size: 24px !important;
    font-weight: 700 !important;
}

/* Optional: enlarge sidebar width */
[data-testid="stSidebar"] {
    min-width: 160px;
    max-width: 300px;
}

</style>
""", unsafe_allow_html=True)



################################################
################## 1st Part ####################
################################################
# Data ingestion and processing

st.set_page_config(
    page_title="KYC Rule Engine - Data Processor",
    layout="wide",
)

st.title("KYC Rule Engine - Data Processor")

st.write(
    "Upload raw KYC partner result data, normalize match states, "
    "and convert it into rule-engine-ready RecordEntry objects."
)


uploaded_file = st.file_uploader(
    "Upload KYC CSV file",
    type=["csv"],
)


if uploaded_file is None:
    st.info("Please upload a CSV file to begin.")
    st.stop()


try:
    raw_df = pd.read_csv(uploaded_file)
except Exception as exc:
    st.error(f"Failed to read CSV file: {exc}")
    st.stop()


try:
    cleaned_df = EP.data_cleaning(raw_df)
    EP.field_validation(cleaned_df)
except Exception as exc:
    st.error(f"Initial validation failed: {exc}")
    st.stop()




st.subheader("Cleaned Data Preview")
st.dataframe(cleaned_df.head(5), width="stretch")


invalid_states = EP.find_invalid_match_states(cleaned_df)

if invalid_states:
    st.warning(f"Found {len(invalid_states)} invalid match state value(s).")
    
    invalid_rows = EP.get_rows_with_invalid_states(cleaned_df, invalid_states)

    st.subheader("Rows With Invalid Match States")
    st.dataframe(invalid_rows, width="stretch")

    if len(invalid_states) > 5:
        st.error(
            "More than 5 unique invalid match states were found. "
            "Processing has stopped. Please clean the file before continuing."
        )
        st.stop()


    valid_options = [state.value for state in Models.MatchFieldState]
    replacements = {}
    
    for invalid_value in sorted(invalid_states):
        replacement = st.selectbox(
            f"Map invalid value `{invalid_value}` to:",
            options=valid_options,
            key=f"replace_{invalid_value}",
        )
        replacements[invalid_value] = replacement

    if st.button("Apply Mapping and Continue"):
        cleaned_df = EP.replace_invalid_states(cleaned_df, replacements)
        st.session_state["cleaned_df"] = cleaned_df
        st.success("Invalid values replaced successfully.")

else:
    st.success("No invalid match states found.")
    st.session_state["cleaned_df"] = cleaned_df



if "cleaned_df" not in st.session_state:
    st.info("Apply mappings before continuing.")
    st.stop()


cleaned_df = st.session_state["cleaned_df"]

st.subheader("Final Normalized Data")
st.dataframe(cleaned_df.head(100),  width="stretch")


if st.button("Build Rule-Ready Records"):
    try:
        records = EP.build_records(cleaned_df)
    except Exception as exc:
        st.error(f"Failed to build records: {exc}")
        st.stop()

    st.success(f"Successfully built {len(records)} records.")

    pickle_buffer = BytesIO()
    pickle.dump(records, pickle_buffer)
    pickle_buffer.seek(0)

    st.download_button(
        label="Download records.pkl",
        data=pickle_buffer,
        file_name="records.pkl",
        mime="application/octet-stream",
    )

    st.subheader("Sample Record Preview")

    if records:
        sample = records[0]
        st.write(f"Record ID: `{sample.record_id}`")
        st.write(f"Data sources: `{list(sample.datasources.keys())}`")

    st.session_state["records"] = records
    st.session_state["data_sources"] = list(sample.datasources.keys())

################################################
################## 2nd Part ####################
################################################
# Rule Processing

st.title("KYC Rule Parser")

st.write("Enter one rule per line.")

rule_input = st.text_area(
    "Rule input",
    height=250,
    value=
    """
    ( (firstinitial or firstname) and notnomatch lastname and (dayofbirth and monthofbirth and yearofbirth) and (address1 or (streetname and streetnumber and (city or postalcode) ) ) )
    ( firstinitial and notnomatch firstname and lastname and taxid )"""
)

if st.button("Parse Rules"):

    try:
        rule_texts = RP.split_rule_input(rule_input)

        parsed_rules = RP.parse_rules(rule_texts)

        st.success(f"Successfully parsed {len(parsed_rules)} unique rule(s).")

        st.subheader("Parsed Rule Logic")

        st.json(parsed_rules)

        st.session_state["parsed_rules"] = parsed_rules


    except Exception as e:
        st.error(f"Failed to parse rules: {e}")


################################################
################## 3rd Part ####################
################################################
# Evaluation

st.title("KYC Rule Evaluation")

cleaned_df = st.session_state.get("cleaned_df")
records = st.session_state.get("records")
parsed_rules = st.session_state.get("parsed_rules")

if cleaned_df is None:
    st.info("Please process data first.")

elif records is None:
    st.info("Please build rule-ready records first.")

elif parsed_rules is None:
    st.info("Please parse rules first.")

else:
    if st.button("Run Evaluation"):

        try:
            evaluation_result = EA.evaluate_records(
                records,
                parsed_rules
            )

            result_df = pd.DataFrame(evaluation_result)

            datasource_counts = (
                cleaned_df
                .groupby("recordid")["datasource"]
                .nunique()
            )

            total_records = len(result_df)
            min_datasources = datasource_counts.min()
            max_datasources = datasource_counts.max()
            verification_rate = result_df["verified"].mean()

            st.session_state["verification_rate"] = verification_rate 
            st.success("Evaluation completed.")
            st.subheader("Evaluation Summary")

            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Evaluation Records", total_records)
            col2.metric("Min Data Sources", min_datasources)
            col3.metric("Max Data Sources", max_datasources)
            col4.metric("Final Passing Rate", f"{verification_rate:.2%}")

            st.subheader("Evaluation Result")
            st.dataframe(result_df, width="stretch")
            
            st.session_state["evaluation_result"] = result_df
            st.session_state["verification_rate"] = verification_rate

        except Exception as exc:
            st.error(f"Evaluation failed: {exc}")