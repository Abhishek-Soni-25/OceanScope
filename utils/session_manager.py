import streamlit as st

class SessionManager:
    @staticmethod
    def initialize_session():
        if 'is_authenticated' not in st.session_state:
            st.session_state.is_authenticated = False
        if 'username' not in st.session_state:
            st.session_state.username = None

    @staticmethod
    def login(username: str):
        st.session_state.is_authenticated = True
        st.session_state.username = username

    @staticmethod
    def logout():
        st.session_state.is_authenticated = False
        st.session_state.username = None

    @staticmethod
    def is_authenticated() -> bool:
        return st.session_state.get('is_authenticated', False)
