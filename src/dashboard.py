import streamlit as st
import pandas as pd
import numpy as np
from datetime import date

# Mapping from provider's short name to key in source data
ALIAS_TO_NAME = {"Lee": "Lee , Jonathan MD"}

def render_sidebar():
    """Render widgets on sidebar for configuring dashboard"""

    st.sidebar.header("Select RVU Data:")

    provider = st.sidebar.selectbox(
        "Provider:", ["Gordon", "Katie", "Lee", "Mike", "Shields"]
    )
    start_date = st.sidebar.date_input("Start Date:", value=date(2020, 1, 1))
    end_date = st.sidebar.date_input("End Date:", value=date.today())

    st.sidebar.header("Compare To:")
    compare_start_date = st.sidebar.date_input("Start Date:", value=date(2020, 1, 1))
    compare_end_date = st.sidebar.date_input("End Date:", value=date.today())


def render():
    """Render streamlit app"""

    # Add sidebar widgets


    provider_key = ALIAS_TO_NAME.get(provider, provider)
