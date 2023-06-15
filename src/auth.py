import os
import streamlit as st


def authenticate():
    """Simple, non-encrypted password authentication stored in streamlit environment and session state"""

    def password_entered():
        """Called when password input changes"""
        if st.session_state["password"] == os.environ["STREAMLIT_PASS"]:
            st.session_state["authn"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["authn"] = False

    if "authn" not in st.session_state:
        # First run, show input for password.
        _, ct, _ = st.columns([1, 2, 1])
        ct.title("RVU Dashboard")
        ct.text_input(
            "Password",
            type="password",
            autocomplete="current-password",
            on_change=password_entered,
            key="password",
        )
        return False
    elif not st.session_state["authn"]:
        # Password not correct, show input + error.
        _, ct, _ = st.columns([1, 2, 1])
        ct.title("RVU Dashboard")
        ct.text_input(
            "Password",
            type="password",
            autocomplete="current-password",
            on_change=password_entered,
            key="password",
        )
        ct.error("Invalid password")
        return False
    else:
        return True
