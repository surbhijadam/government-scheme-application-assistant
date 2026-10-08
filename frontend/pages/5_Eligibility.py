import streamlit as st

import api_client

st.set_page_config(page_title="Eligibility Check", page_icon="✅")
st.title("✅ Eligibility Check")

if not st.session_state.get("token"):
    st.warning("Please log in first (see the Login page in the sidebar).")
    st.stop()

schemes_data, error = api_client.list_schemes()
if error:
    st.error(error)
    st.stop()

if schemes_data is None:
    st.error("Could not load available schemes right now. Please try again.")
    st.stop()

if schemes_data.get("count", 0) == 0:
    st.info("No schemes are available to check yet.")
    st.stop()

scheme_options = {s["name"]: s["scheme_id"] for s in schemes_data.get("schemes", [])}
if not scheme_options:
    st.info("No schemes are available to check yet.")
    st.stop()

selected_name = st.selectbox("Choose a scheme to check", list(scheme_options.keys()))

if st.button("Check My Eligibility"):
    scheme_id = scheme_options[selected_name]
    result, error = api_client.check_eligibility(scheme_id)

    if error:
        st.error(error)
        if "profile" in error.lower():
            st.info("Go to the Profile page to fill in your details first.")
    else:
        if result is None:
            st.error("Eligibility check returned no data. Please try again.")
            st.stop()

        scheme_name = result.get("scheme_name", selected_name)
        if result.get("eligible"):
            st.success(f"🎉 You ARE eligible for **{scheme_name}**!")
        else:
            st.error(f"You are NOT currently eligible for **{scheme_name}**.")

        if result.get("matched_rules"):
            st.subheader("✅ Requirements you meet")
            for rule in result["matched_rules"]:
                st.write(f"- {rule['field_name']} {rule['operator']} {rule['expected_value']} (your value: {rule['your_value']})")

        if result.get("failed_rules"):
            st.subheader("❌ Requirements you don't meet")
            for rule in result["failed_rules"]:
                st.write(f"- {rule['reason']}")