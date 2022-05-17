import streamlit as st

def authenticate():
    """Simple, non-encrypted password authentication stored in streamlit environment and session state"""

    def password_entered():
        """Called when password input changes"""
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["authn"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["authn"] = False

    if "authn" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["authn"]:
        # Password not correct, show input + error.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("Invalid password")
        return False
    else:
        return True
