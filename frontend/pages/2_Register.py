import streamlit as st

import api_client

st.set_page_config(page_title="Register", page_icon="📝")
st.title("📝 Register")

if st.session_state.get("token"):
    st.info("You're already logged in. Log out first if you want to create a different account.")
else:
    with st.form("register_form"):
        name = st.text_input("Full name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password", help="At least 8 characters")
        submitted = st.form_submit_button("Register")

    if submitted:
        if not name or not email or not password:
            st.error("Please fill in all fields.")
        else:
            data, error = api_client.register(name, email, password)
            if error:
                st.error(error)
            else:
                st.success("Registration successful! Go to the Login page to log in.")