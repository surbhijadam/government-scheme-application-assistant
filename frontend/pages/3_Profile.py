import streamlit as st

import api_client

st.set_page_config(page_title="Profile", page_icon="👤")
st.title("👤 My Profile")

if not st.session_state.get("token"):
    st.warning("Please log in first (see the Login page in the sidebar).")
    st.stop()

GENDER_OPTIONS = ["", "Male", "Female", "Other"]
CATEGORY_OPTIONS = ["", "General", "OBC", "SC", "ST", "EWS"]

existing_profile, error = api_client.get_profile()
if error and "not found" not in error.lower():
    st.error(error)
    existing_profile = {}
existing_profile = existing_profile or {}

st.caption("This information is used to check your eligibility for schemes - it's never shared publicly.")

with st.form("profile_form"):
    age = st.number_input("Age", min_value=0, max_value=120, value=existing_profile.get("age") or 0, step=1)
    gender = st.selectbox("Gender", GENDER_OPTIONS, index=GENDER_OPTIONS.index(existing_profile.get("gender") or ""))
    state = st.text_input("State", value=existing_profile.get("state") or "")
    income = st.number_input(
        "Annual income (₹)", min_value=0.0, value=float(existing_profile.get("income") or 0), step=1000.0
    )
    occupation = st.text_input("Occupation", value=existing_profile.get("occupation") or "")
    category = st.selectbox(
        "Category", CATEGORY_OPTIONS, index=CATEGORY_OPTIONS.index(existing_profile.get("category") or "")
    )
    other_details = st.text_area("Other details (optional)", value=existing_profile.get("other_details") or "")

    submitted = st.form_submit_button("Save Profile")

if submitted:
    payload = {
        "age": int(age),
        "income": float(income),
        "state": state.strip(),
        "occupation": occupation.strip(),
        "other_details": other_details.strip(),
    }
    if gender:
        payload["gender"] = gender
    if category:
        payload["category"] = category

    data, error = api_client.update_profile(payload)
    if error:
        st.error(error)
    else:
        st.success("Profile saved!")
        st.rerun()