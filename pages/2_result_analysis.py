import streamlit as st

import core.engine_analyzer as Analyzer


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

st.title("KYC Result Analysis")
st.write("Analyze datasource utilization from verified KYC results.")


if "evaluation_result" not in st.session_state:
    st.warning("No evaluation result found. Please run the evaluation first.")
    st.stop()


evaluation_result = st.session_state["evaluation_result"]

st.subheader("Evaluation Summary")
col1, col2, col3, col4 = st.columns(4)

total_records = st.session_state["total_records"]
min_datasources = st.session_state["min_datasources"]
max_datasources = st.session_state["max_datasources"]
verification_rate = st.session_state["verification_rate"]


col1.metric("Evaluation Records", total_records)
col2.metric("Min Data Sources", min_datasources)
col3.metric("Max Data Sources", max_datasources)
col4.metric("Final Passing Rate", f"{verification_rate:.2%}")


st.subheader("Evaluation Result Preview")
st.dataframe(evaluation_result.head(3), width='stretch')


try:
    # verified_result = Analyzer.filter_verified_result(evaluation_result)
    ds_counter = Analyzer.datasource_utilization_count(evaluation_result)
    utilization_df = Analyzer.counter_to_dataframe(ds_counter)

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