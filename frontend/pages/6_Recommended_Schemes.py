import streamlit as st

import api_client

st.set_page_config(page_title="Recommended Schemes", page_icon="⭐")
st.title("⭐ Recommended Schemes")
st.caption("Schemes you currently qualify for, based on your profile.")

if not st.session_state.get("token"):
    st.warning("Please log in first (see the Login page in the sidebar).")
    st.stop()

data, error = api_client.get_recommendations()

if error:
    st.error(error)
    if "profile" in error.lower():
        st.info("Go to the Profile page to fill in your details first.")
    st.stop()

if not data:
    st.warning("Recommendations are unavailable right now. Please try again later.")
    st.stop()

count = data.get("count", 0)
recommendations = data.get("recommendations", [])

if count == 0:
    st.info("No schemes match your profile yet. Try updating your profile, or check back later as new schemes are added.")
else:
    st.success(f"You're eligible for {count} scheme(s)!")
    for scheme in recommendations:
        with st.container(border=True):
            st.subheader(scheme["name"])
            st.caption(scheme.get("category") or "Uncategorized")
            st.write(scheme["description"] or "No description available.")

            deadline = scheme.get("deadline")
            days_remaining = scheme.get("days_remaining")
            deadline_status = scheme.get("deadline_status")
            deadline_warning = scheme.get("deadline_warning", False)

            if deadline:
                st.write(f"**Application Deadline:** {deadline}")

                if days_remaining is not None:
                    if deadline_status == "passed":
                        st.error("Application deadline has passed.")
                    elif deadline_status == "today":
                        st.warning("Application deadline is today.")
                    elif deadline_warning:
                        st.warning(f"Application deadline is in {days_remaining} days.")
                    else:
                        st.info(f"Application deadline is in {days_remaining} days.")
            else:
                st.write("**Application Deadline:** Not specified")

            with st.expander("Why you qualify"):
                for rule in scheme.get("matched_rules", []):
                    st.write(f"- {rule['field_name']} {rule['operator']} {rule['expected_value']} ✓")