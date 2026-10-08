import streamlit as st

import api_client

st.set_page_config(page_title="Apply", page_icon="📨")
st.title("📨 Apply for a Scheme")

if not st.session_state.get("token"):
    st.warning("Please log in first (see the Login page in the sidebar).")
    st.stop()

schemes_data, error = api_client.list_schemes()
if error:
    st.error(error)
    st.stop()

if schemes_data is None:
    st.error("Unable to load available schemes right now.")
    st.stop()

if schemes_data.get("count", 0) == 0:
    st.info("No schemes are available to apply to yet.")
    st.stop()

schemes = schemes_data.get("schemes", [])
scheme_options = {s["name"]: s["scheme_id"] for s in schemes}

selected_name = st.selectbox(
    "Choose a scheme to apply for",
    list(scheme_options.keys()),
)

selected_scheme = next(
    scheme for scheme in schemes
    if scheme["scheme_id"] == scheme_options[selected_name]
)

st.caption(
    "This starts a draft application. You can upload documents and "
    "submit it later from My Applications."
)

deadline = selected_scheme.get("deadline")
days_remaining = selected_scheme.get("days_remaining")
deadline_status = selected_scheme.get("deadline_status")
deadline_warning = selected_scheme.get("deadline_warning", False)

if deadline:
    st.write(f"**Application Deadline:** {deadline}")

    if deadline_status == "passed":
        st.error(
            "Application deadline has passed. "
            "You cannot start a new application."
        )
    elif deadline_status == "today":
        st.warning("Application deadline is today.")
    elif deadline_warning:
        st.warning(
            f"Application deadline is in {days_remaining} days."
        )
    else:
        st.info(
            f"Application deadline is in {days_remaining} days."
        )
else:
    st.write("**Application Deadline:** Not specified")


if deadline_status != "passed":
    if st.button("Start Application"):
        scheme_id = scheme_options[selected_name]
        data, error = api_client.create_application(scheme_id)

        if error:
            st.error(error)

            if data and "application_id" in data:
                st.info(
                    f"You already have application #{data['application_id']} "
                    "for this scheme. Go to My Applications to continue "
                    "working on it."
                )
        else:
            scheme_name = (
                data.get("scheme_name", selected_name)
                if data
                else selected_name
            )

            st.success(
                f"Draft application created for **{scheme_name}**!"
            )
            st.info(
                "Go to the My Applications page to upload documents "
                "and submit it."
            )