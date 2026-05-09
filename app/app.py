import pickle
from io import BytesIO

import pandas as pd
import streamlit as st

import core.engine as Engine
from core.models import MatchFieldState


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