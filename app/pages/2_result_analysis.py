import streamlit as st
import pandas as pd

import core.engine_analyzer as Analyzer


st.set_page_config(
    page_title="KYC Result Analysis",
    layout="wide"
)

st.title("KYC Result Analysis")
st.write("Analyze datasource utilization from verified KYC results.")


if "evaluation_result" not in st.session_state:
    st.warning("No evaluation result found. Please run the evaluation first.")
    st.stop()


evaluation_result = st.session_state["evaluation_result"]

st.subheader("Evaluation Result Preview")
st.dataframe(evaluation_result.head(5), width='stretch')


try:
    ds_counter = Analyzer.datasource_utilization_count(evaluation_result)
    utilization_df = Analyzer.counter_to_dataframe(ds_counter)

    st.write("Utilization dataframe:")
    st.dataframe(utilization_df.head(), width='stretch')

    st.subheader("Datasource Utilization")

    if utilization_df.empty:
        st.info("No verified records with datasource assignments found.")
        st.stop()

    st.bar_chart(
        utilization_df,
        x="datasource",
        y="usage_count"
    )

    st.subheader("Datasource Usage Table")
    st.dataframe(utilization_df, use_container_width=True)

except Exception as e:
    st.error(f"Failed to analyze evaluation result: {e}")