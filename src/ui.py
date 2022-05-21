import streamlit as st
import pandas as pd
import numpy as np
from datetime import date
from .auth import authenticate

# Mapping from provider's short name to key in source data
ALIAS_TO_NAME = {"Lee": "Lee , Jonathan MD"}


def sidebar():
    """Render widgets on sidebar for configuring dashboard"""

    # Filter options by provider and dates
    st.sidebar.subheader("Select Provider and Dates:")
    provider = st.sidebar.selectbox(
        "Provider:", ["Gordon", "Katie", "Lee", "Mike", "Shields"]
    )
    start_date = st.sidebar.date_input("Start Date:", value=date(2020, 1, 1))
    end_date = st.sidebar.date_input("End Date:", value=date.today())

    # Option to compare to another date range
    compare = st.sidebar.checkbox("Compare to different date range")
    if compare:
        st.sidebar.subheader("Compare To:")
        compare_start_date = st.sidebar.date_input(
            "Start Date:", key="compare_start", value=date(2020, 1, 1)
        )
        compare_end_date = st.sidebar.date_input(
            "End Date:", key="compare_end", value=date.today()
        )


def render():
    """Main streamlit app entry point"""

    st.title("RVU Dashboard")

    # Authenticate user
    if not authenticate():
        st.stop()

    # Add sidebar widgets
    sidebar()
