import streamlit as st

import api_client

st.set_page_config(page_title="My Applications", page_icon="🗂️")

if not st.session_state.get("token"):
    st.warning("Please log in first (see the Login page in the sidebar).")
    st.stop()

if "viewing_application_id" not in st.session_state:
    st.session_state.viewing_application_id = None

STATUS_COLORS = {
    "draft": "⚪",
    "submitted": "🔵",
    "under_review": "🟡",
    "additional_info_required": "🟠",
    "approved": "🟢",
    "rejected": "🔴",
    "withdrawn": "⚫",
}


def show_application_list():
    st.title("🗂️ My Applications")

    data, error = api_client.list_applications()
    if error:
        st.error(error)
        return

    if data is None:
        st.info("No applications found.")
        return

    if data.get("count", 0) == 0:
        st.info("You haven't started any applications yet. Visit the Apply page to get started.")
        return

    for application in data.get("applications", []):
        with st.container(border=True):
            icon = STATUS_COLORS.get(application["status"], "⚪")
            st.subheader(f"{icon} {application['scheme_name']}")
            st.caption(f"Status: {application['status'].replace('_', ' ').title()}")
            if st.button("View Details", key=f"view_app_{application['application_id']}"):
                st.session_state.viewing_application_id = application["application_id"]
                st.rerun()


def show_application_detail():
    application_id = st.session_state.viewing_application_id

    if st.button("← Back to My Applications"):
        st.session_state.viewing_application_id = None
        st.rerun()

    status_data, error = api_client.get_application_status(application_id)
    if error:
        st.error(error)
        return

    if status_data is None:
        st.error("Application details could not be loaded.")
        return

    st.title(status_data["scheme_name"])
    is_draft = status_data["current_status"] == "draft"
    icon = STATUS_COLORS.get(status_data["current_status"], "⚪")
    st.subheader(f"{icon} Current status: {status_data['current_status'].replace('_', ' ').title()}")

    st.markdown("#### Status History")
    for entry in status_data.get("status_history", []):
        when = entry["updated_at"].split("T")[0] if entry.get("updated_at") else ""
        st.write(f"- **{entry['status'].replace('_', ' ').title()}** ({when}) — {entry.get('remarks', '')}")

    if is_draft:
        st.divider()
        st.markdown("#### Required Documents")

        checklist_data, error = api_client.get_document_checklist(application_id)
        if error:
            st.error(error)
        else:
            if checklist_data is None:
                st.info("No document checklist is available for this application.")
            else:
                for item in checklist_data.get("checklist", []):
                    mandatory_tag = "Mandatory" if item["mandatory"] else "Optional"
                    if item["uploaded"]:
                        st.success(f"✅ {item['document_name']} ({mandatory_tag}) — {item['file']['original_filename']}")
                    else:
                        st.warning(f"⬜ {item['document_name']} ({mandatory_tag}) — not uploaded")

                    uploaded_file = st.file_uploader(
                        f"Upload {item['document_name']}",
                        type=["pdf", "jpg", "jpeg", "png"],
                        key=f"upload_{application_id}_{item['document_id']}",
                    )
                    if uploaded_file and st.button("Save this file", key=f"save_{application_id}_{item['document_id']}"):
                        result, upload_error = api_client.upload_document(application_id, item["document_id"], uploaded_file)
                        if upload_error:
                            st.error(upload_error)
                        else:
                            uploaded_name = "uploaded file"
                            if isinstance(result, dict):
                                uploaded_name = (
                                    result.get("original_filename")
                                    or result.get("filename")
                                    or uploaded_name
                                )
                            st.success(f"Uploaded {uploaded_name}!")
                            st.rerun()

        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Submit Application", type="primary"):
                result, submit_error = api_client.submit_application(application_id)
                if submit_error:
                    st.error(submit_error)
                else:
                    st.success("Application submitted!")
                    st.rerun()
        with col2:
            if st.button("Withdraw Draft"):
                result, withdraw_error = api_client.withdraw_application(application_id)
                if withdraw_error:
                    st.error(withdraw_error)
                else:
                    st.info("Application withdrawn.")
                    st.rerun()


if st.session_state.viewing_application_id:
    show_application_detail()
else:
    show_application_list()