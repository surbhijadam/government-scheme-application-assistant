import streamlit as st

import api_client


st.set_page_config(
    page_title="Government Scheme Assistant",
    page_icon="🏛️",
)


# ---------------------------------------------------------
# Session state
# ---------------------------------------------------------

if "token" not in st.session_state:
    st.session_state.token = None
    st.session_state.user = None


# ---------------------------------------------------------
# Page title
# ---------------------------------------------------------

st.title("🏛️ Government Scheme Application Assistant")


# ---------------------------------------------------------
# Disclaimer
# ---------------------------------------------------------

st.warning(
    "**This is a learning/portfolio project, not an official government portal.** "
    "Scheme data shown here is sample/demo data for demonstration purposes only."
)


# ---------------------------------------------------------
# Login status
# ---------------------------------------------------------

if st.session_state.token and st.session_state.user:

    st.success(
        f"Logged in as **{st.session_state.user.get('name', 'User')}** "
        f"({st.session_state.user.get('email', 'unknown email')})"
    )

    st.write(
        "Use the sidebar to navigate to your profile, browse schemes, "
        "or check your applications."
    )

else:

    st.info(
        "Please log in or register using the sidebar to get started."
    )


# ---------------------------------------------------------
# Deadline reminders
# ---------------------------------------------------------

st.markdown("### 📅 Scheme Deadline Reminders")

schemes_data, error = api_client.list_schemes()

if error:

    st.info(
        "Deadline reminders are currently unavailable."
    )

elif schemes_data is None:

    st.info(
        "No scheme information is currently available."
    )

else:

    schemes = schemes_data.get("schemes", [])

    approaching_schemes = [
        scheme
        for scheme in schemes
        if scheme.get("deadline_warning") is True
        and scheme.get("days_remaining") is not None
        and scheme.get("days_remaining") >= 0
    ]

    if not approaching_schemes:

        st.success(
            "No scheme deadlines are approaching within the next 7 days."
        )

    else:

        # Show the nearest deadlines first.
        approaching_schemes.sort(
            key=lambda scheme: scheme["days_remaining"]
        )

        for scheme in approaching_schemes:

            scheme_name = scheme.get(
                "name",
                "Unnamed scheme",
            )

            days_remaining = scheme.get(
                "days_remaining"
            )

            deadline = scheme.get(
                "deadline"
            )

            if days_remaining == 0:

                st.error(
                    f"🚨 **{scheme_name}** — "
                    f"application deadline is **today** "
                    f"({deadline})."
                )

            elif days_remaining == 1:

                st.warning(
                    f"⚠️ **{scheme_name}** — "
                    f"application deadline is **tomorrow** "
                    f"({deadline})."
                )

            else:

                st.warning(
                    f"⚠️ **{scheme_name}** — "
                    f"application deadline is in "
                    f"**{days_remaining} days** "
                    f"({deadline})."
                )


# ---------------------------------------------------------
# Application features
# ---------------------------------------------------------

st.markdown(
    """
    ### What this app does
    - Browse sample government schemes
    - Check your eligibility using a transparent, rule-based engine (no AI guesswork)
    - Apply, track your application status, and manage required documents
    """
)