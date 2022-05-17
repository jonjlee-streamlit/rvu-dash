import streamlit as st
from src.auth import authenticate
from src import dashboard

st.title("RVU Dashboard")

# Authenticate user
if not authenticate():
    st.stop()

# Render main app
dashboard.render()
