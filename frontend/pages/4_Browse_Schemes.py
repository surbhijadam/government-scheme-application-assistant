import streamlit as st

import api_client

st.set_page_config(page_title="Browse Schemes", page_icon="📋")

if "selected_scheme_id" not in st.session_state:
    st.session_state.selected_scheme_id = None


def show_scheme_list():
    st.title("📋 Browse Schemes")

    col1, col2 = st.columns(2)
    search = col1.text_input("Search by name")
    category = col2.text_input("Filter by category")

    data, error = api_client.list_schemes(search=search, category=category)
    if error or data is None:
        st.error(error or "Unable to load schemes right now.")
        return

    if data.get("count", 0) == 0:
        st.info("No schemes match your search.")
        return

    for scheme in data["schemes"]:
        with st.container(border=True):
            st.subheader(scheme.get("name") or "Unnamed Scheme")
            st.caption(scheme.get("category") or "Uncategorized")
            st.write(scheme.get("description") or "No description available.")

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

            if st.button("View Details", key=f"view_{scheme['scheme_id']}"):
                st.session_state.selected_scheme_id = scheme["scheme_id"]
                st.rerun()


def show_scheme_detail():
    scheme_id = st.session_state.selected_scheme_id

    if st.button("← Back to all schemes"):
        st.session_state.selected_scheme_id = None
        st.rerun()

    data, error = api_client.get_scheme(scheme_id)
    if error or data is None:
        st.error(error or "Unable to load the scheme details right now.")
        return

    st.title(data.get("name", "Scheme Details"))
    st.caption(data.get("category") or "Uncategorized")
    st.write(data.get("description") or "No description available.")

    if data.get("benefits"):
        st.subheader("Benefits")
        st.write(data["benefits"])

    st.subheader("Eligibility Rules")
    if data.get("eligibility_rules"):
        for rule in data["eligibility_rules"]:
            st.write(f"- {rule['field_name']} {rule['operator']} {rule['expected_value']}")
    else:
        st.write("No specific eligibility rules for this scheme.")

    st.subheader("Required Documents")
    if data.get("required_documents"):
        for doc in data["required_documents"]:
            tag = "Mandatory" if doc["mandatory"] else "Optional"
            st.write(f"- {doc['document_name']} ({tag})")
    else:
        st.write("No documents required.")


if st.session_state.selected_scheme_id:
    show_scheme_detail()
else:
    show_scheme_list()