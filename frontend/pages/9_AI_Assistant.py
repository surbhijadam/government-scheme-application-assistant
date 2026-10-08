import streamlit as st

import api_client

st.set_page_config(page_title="AI Assistant", page_icon="🤖")
st.title("🤖 AI Assistant")

if not st.session_state.get("token"):
    st.warning("Please log in first (see the Login page in the sidebar).")
    st.stop()

st.info(
    "This assistant explains scheme details and documents in plain language. "
    "It is an AI assistant for a demo project, **not an official government authority**, "
    "and it never decides your eligibility - use the Eligibility Check page for that."
)

schemes_data, error = api_client.list_schemes()
scheme_options = {"(General question - no specific scheme)": None}
if not error and isinstance(schemes_data, dict):
    schemes = schemes_data.get("schemes") or []
    scheme_options.update(
        {
            s["name"]: s["scheme_id"]
            for s in schemes
            if isinstance(s, dict) and "name" in s and "scheme_id" in s
        }
    )

selected_scheme_name = st.selectbox("Ask about a specific scheme (optional)", list(scheme_options.keys()))
selected_scheme_id = scheme_options[selected_scheme_name]

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for role, text in st.session_state.chat_history:
    with st.chat_message(role):
        st.write(text)

user_message = st.chat_input("Ask a question about schemes, eligibility, or documents...")

if user_message:
    st.session_state.chat_history.append(("user", user_message))
    with st.chat_message("user"):
        st.write(user_message)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            data, error = api_client.ask_assistant(user_message, scheme_id=selected_scheme_id)

        if error or data is None:
            message = error or "Unable to get a response from the assistant."
            st.error(message)
            st.session_state.chat_history.append(("assistant", f"⚠️ {message}"))
        else:
            reply = data.get("reply", "")
            disclaimer = data.get("disclaimer", "")
            st.write(reply)
            if disclaimer:
                st.caption(disclaimer)
            st.session_state.chat_history.append(("assistant", reply))