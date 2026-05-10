import pickle
from io import BytesIO

import pandas as pd
import streamlit as st

import core.engine_processor as EP
import core.models as Models


################################################
################## First Page ##################
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
st.dataframe(cleaned_df.head(5), use_container_width=True)


invalid_states = EP.find_invalid_match_states(cleaned_df)

if invalid_states:
    st.warning(f"Found {len(invalid_states)} invalid match state value(s).")
    
    invalid_rows = EP.get_rows_with_invalid_states(cleaned_df, invalid_states)

    st.subheader("Rows With Invalid Match States")
    st.dataframe(invalid_rows, use_container_width=True)

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


final_df = st.session_state["cleaned_df"]

st.subheader("Final Normalized Data")
st.dataframe(final_df.head(100), use_container_width=True)


if st.button("Build Rule-Ready Records"):
    try:
        records = EP.build_records(final_df)
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
        st.write(f"Datasources: `{list(sample.datasources.keys())}`")