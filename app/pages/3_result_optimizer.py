import json
import streamlit as st

import core.engine_analyzer as Analyzer
import core.engine_optimizer as Optimizer


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



st.title("KYC Cost Optimizer")
st.write("Input datasource costs and solve the minimum-cost source selection problem.")


if "evaluation_result" not in st.session_state:
    st.warning("No evaluation result found. Please run rule evaluation first.")
    st.stop()


evaluation_result = st.session_state["evaluation_result"]

st.subheader("Evaluation Result Preview")
st.dataframe(evaluation_result.head(3), use_container_width=True)


if "rule_results" not in evaluation_result.columns:
    st.error("Missing rule_results column from evaluation_result.")
    st.stop()


# available_datasources = st.session_state["data_sources"]
# available_datasources = sorted(available_datasources)

available_datasources = Optimizer.get_available_sources(evaluation_result)

if not available_datasources:
    st.warning("No available datasources found from rule_results.")
    st.stop()


# -----------------------------
# Cost input
# -----------------------------

st.subheader("Datasource Cost Mapping")
st.write("Enter the cost for each available datasource.")

source_cost = {}

cols = st.columns(3)

for i, datasource in enumerate(available_datasources):
    with cols[i % 3]:
        st.markdown(f"**{datasource}**")

        source_cost[datasource] = st.number_input(
            label=f"Cost",
            min_value=0.0,
            value=0.0,
            step=0.01,
            key=f"cost_{datasource}"
        )


st.subheader("Cost Mapping Preview")
st.json(source_cost)

st.subheader("Optimization Settings")

verification_rate = st.session_state["verification_rate"]

min_verify_rate = st.slider(
    "Minimum verification rate",
    min_value=0.00,
    max_value=round(verification_rate,2),
    value=verification_rate,
    step=0.025
)

time_limit_sec = st.number_input(
    "Solver time limit in seconds",
    min_value=1,
    value=60,
    step=10
)




# -----------------------------
# Run optimizer
# -----------------------------

if st.button("Run Optimizer"):

    try:
        optimizer_result = Optimizer.solve_source_selection_pulp(
            df=evaluation_result,
            source_cost=source_cost,
            min_verify_rate=min_verify_rate,
            time_limit_sec=time_limit_sec
        )

        st.session_state["optimizer_result"] = optimizer_result

        st.subheader("Optimizer Status")
        st.write(optimizer_result["status"])

        if optimizer_result["status"] == "NO_SOLUTION":
            st.error(
                f"No solution found. Solver status: "
                f"{optimizer_result.get('solver_status')}"
            )
            st.stop()

        st.success("Optimization completed.")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Required Verified",
            optimizer_result["required_verified"]
        )

        col2.metric(
            "Actual Verified",
            optimizer_result["actual_verified"]
        )

        col3.metric(
            "Actual Verify Rate",
            round(optimizer_result["actual_verify_rate"], 4)
        )

        col4.metric(
            "Cost Per Record",
            optimizer_result["cost_per_record"]
        )

        st.subheader("Selected Sources")
        st.write(optimizer_result["selected_sources"])

        st.subheader("Total Cost")
        st.metric("Total Cost", optimizer_result["total_cost"])

        st.subheader("Verified Record IDs")
        st.write(optimizer_result["verified_record_ids"])

        st.subheader("Unverified Record IDs")
        st.write(optimizer_result["unverified_record_ids"])

        st.subheader("Assignments")
        st.json(optimizer_result["assignments"])

    except Exception as e:
        st.error(f"Failed to run optimizer: {e}")