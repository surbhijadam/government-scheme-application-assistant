import streamlit as st
from datetime import date

import api_client


st.set_page_config(
    page_title="Admin Dashboard",
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ Admin Dashboard")


# ---------------------------------------------------------
# Authentication and authorization
# ---------------------------------------------------------

if not st.session_state.get("token"):
    st.warning(
        "Please log in first (see the Login page in the sidebar)."
    )
    st.stop()


if st.session_state.get("user", {}).get("role") != "admin":
    st.error(
        "Admin access required. This page is only visible to admin accounts."
    )
    st.stop()


# ---------------------------------------------------------
# Constants
# ---------------------------------------------------------

ALL_STATUSES = [
    "",
    "draft",
    "submitted",
    "under_review",
    "additional_info_required",
    "approved",
    "rejected",
    "withdrawn",
]

OPERATORS = [
    "",
    "==",
    "!=",
    ">",
    ">=",
    "<",
    "<=",
]


# ---------------------------------------------------------
# Tabs
# ---------------------------------------------------------

tab_applications, tab_schemes = st.tabs(
    ["📄 Applications", "📋 Schemes"]
)


# =========================================================
# APPLICATIONS TAB
# =========================================================

with tab_applications:

    status_filter = st.selectbox(
        "Filter by status",
        ALL_STATUSES,
        key="admin_status_filter",
    )

    data, error = api_client.admin_list_applications(
        status_filter
    )

    if error:
        st.error(error)

    elif data is None:
        st.warning("No application data returned.")

    elif data.get("count", 0) == 0:
        st.info("No applications match this filter.")

    else:
        for application in data.get("applications", []):

            with st.container(border=True):

                col1, col2 = st.columns([3, 2])

                with col1:
                    st.subheader(
                        application["scheme_name"]
                    )

                    st.caption(
                        f"Applicant: "
                        f"{application['applicant_name']} "
                        f"({application['applicant_email']})"
                    )

                    st.write(
                        "Current status: "
                        f"**{application['status'].replace('_', ' ').title()}**"
                    )

                with col2:

                    new_status = st.selectbox(
                        "Move to",
                        [
                            "",
                            "under_review",
                            "additional_info_required",
                            "approved",
                            "rejected",
                        ],
                        key=(
                            f"status_select_"
                            f"{application['application_id']}"
                        ),
                    )

                    remarks = st.text_input(
                        "Remarks",
                        key=(
                            f"remarks_"
                            f"{application['application_id']}"
                        ),
                    )

                    if st.button(
                        "Update Status",
                        key=(
                            f"update_"
                            f"{application['application_id']}"
                        ),
                    ):

                        if not new_status:
                            st.warning(
                                "Choose a status first."
                            )

                        else:

                            result, update_error = (
                                api_client.admin_update_application_status(
                                    application["application_id"],
                                    new_status,
                                    remarks,
                                )
                            )

                            if update_error:
                                st.error(update_error)

                            else:
                                st.success(
                                    f"Status updated to {new_status}."
                                )
                                st.rerun()


# =========================================================
# SCHEMES TAB
# =========================================================

with tab_schemes:

    # -----------------------------------------------------
    # Create New Scheme
    # -----------------------------------------------------

    st.markdown("### Create a New Scheme")

    with st.form("create_scheme_form"):

        name = st.text_input("Scheme name")

        description = st.text_area(
            "Description"
        )

        category = st.text_input(
            "Category"
        )

        set_deadline = st.checkbox(
            "Set an application deadline",
            key="create_set_deadline",
        )

        deadline = None

        if set_deadline:

            deadline = st.date_input(
                "Application deadline",
                min_value=date.today(),
                key="create_deadline",
            )

        submitted = st.form_submit_button(
            "Create Scheme"
        )

    if submitted:

        if not name:
            st.error("Name is required.")

        else:

            scheme_data = {
                "name": name,
                "description": description,
                "category": category,
            }

            if set_deadline and deadline:
                scheme_data["deadline"] = (
                    deadline.isoformat()
                )

            data, error = api_client.admin_create_scheme(
                scheme_data
            )

            if error:
                st.error(error)

            elif data is not None:

                scheme_id = data.get(
                    "scheme_id"
                )

                scheme_name = data.get(
                    "name"
                ) or "Untitled scheme"

                if scheme_id is not None:

                    st.success(
                        f"Created scheme #{scheme_id}: "
                        f"{scheme_name}"
                    )

                else:

                    st.success(
                        f"Created scheme: {scheme_name}"
                    )

                st.rerun()

            else:

                st.success(
                    "Scheme created successfully."
                )

                st.rerun()


    # -----------------------------------------------------
    # Existing Schemes
    # -----------------------------------------------------

    st.divider()

    st.markdown(
        "### Manage Existing Schemes"
    )

    schemes_data, error = api_client.list_schemes()

    if error:
        st.error(error)

    elif schemes_data is None:
        st.warning(
            "No scheme data returned."
        )

    else:

        schemes = schemes_data.get(
            "schemes",
            []
        )

        if not schemes:

            st.info(
                "No schemes found."
            )

        else:

            for scheme in schemes:

                detail = None
                detail_error = None

                with st.expander(
                    f"{scheme['name']} "
                    f"({scheme['category'] or 'Uncategorized'})"
                ):

                    # -------------------------------------
                    # Get full scheme details
                    # -------------------------------------

                    detail, detail_error = (
                        api_client.get_scheme(
                            scheme["scheme_id"]
                        )
                    )

                    if detail_error:
                        st.error(detail_error)
                        st.stop()

                    if detail is None:
                        st.warning(
                            "No details returned for this scheme."
                        )
                        st.stop()


                    # -------------------------------------
                    # Deadline Management
                    # -------------------------------------

                    st.markdown(
                        "**Application Deadline**"
                    )

                    current_deadline = detail.get(
                        "deadline"
                    )

                    if current_deadline:

                        st.write(
                            "Current deadline: "
                            f"**{current_deadline}**"
                        )

                    else:

                        st.write(
                            "Current deadline: "
                            "**Not specified**"
                        )


                    remove_deadline = st.checkbox(
                        "Remove deadline",
                        key=(
                            f"remove_deadline_"
                            f"{scheme['scheme_id']}"
                        ),
                    )


                    if remove_deadline:

                        deadline_value = None

                    elif current_deadline:

                        deadline_value = st.date_input(
                            "Application deadline",
                            value=date.fromisoformat(
                                current_deadline
                            ),
                            key=(
                                f"deadline_"
                                f"{scheme['scheme_id']}"
                            ),
                        )

                    else:

                        deadline_value = st.date_input(
                            "Application deadline",
                            min_value=date.today(),
                            key=(
                                f"deadline_"
                                f"{scheme['scheme_id']}"
                            ),
                        )


                    if st.button(
                        "Save Deadline",
                        key=(
                            f"save_deadline_"
                            f"{scheme['scheme_id']}"
                        ),
                    ):

                        if remove_deadline:

                            updates = {
                                "deadline": None
                            }

                        elif deadline_value is not None:

                            updates = {
                                "deadline": (
                                    deadline_value.isoformat()
                                )
                            }

                        else:

                            st.warning(
                                "Please select a valid application deadline."
                            )
                            st.stop()


                        result, update_error = (
                            api_client.admin_update_scheme(
                                scheme["scheme_id"],
                                updates,
                            )
                        )


                        if update_error:

                            st.error(
                                update_error
                            )

                        else:

                            st.success(
                                "Application deadline updated."
                            )

                            st.rerun()


                    st.divider()


                    # -------------------------------------
                    # Scheme Status
                    # -------------------------------------

                    toggle_label = (
                        "Deactivate"
                        if detail.get("status") == "active"
                        else "Activate"
                    )

                    if st.button(
                        toggle_label,
                        key=(
                            f"toggle_"
                            f"{scheme['scheme_id']}"
                        ),
                    ):

                        new_status = (
                            "inactive"
                            if detail.get("status") == "active"
                            else "active"
                        )

                        api_client.admin_update_scheme(
                            scheme["scheme_id"],
                            {
                                "status": new_status
                            },
                        )

                        st.rerun()


                    # -------------------------------------
                    # Eligibility Rules
                    # -------------------------------------

                    st.markdown(
                        "**Eligibility Rules**"
                    )

                    for rule in detail.get(
                        "eligibility_rules",
                        [],
                    ):

                        rule_col1, rule_col2 = (
                            st.columns([4, 1])
                        )

                        rule_col1.write(
                            f"{rule['field_name']} "
                            f"{rule['operator']} "
                            f"{rule['expected_value']}"
                        )

                        if rule_col2.button(
                            "Delete",
                            key=(
                                f"delrule_"
                                f"{scheme['scheme_id']}_"
                                f"{rule['rule_id']}"
                            ),
                        ):

                            api_client.admin_delete_rule(
                                scheme["scheme_id"],
                                rule["rule_id"],
                            )

                            st.rerun()


                    with st.form(
                        f"add_rule_form_{scheme['scheme_id']}"
                    ):

                        rule_col1, rule_col2, rule_col3 = (
                            st.columns(3)
                        )

                        field_name = rule_col1.text_input(
                            "Field",
                            key=(
                                f"field_"
                                f"{scheme['scheme_id']}"
                            ),
                        )

                        operator_symbol = rule_col2.selectbox(
                            "Operator",
                            OPERATORS,
                            key=(
                                f"op_"
                                f"{scheme['scheme_id']}"
                            ),
                        )

                        expected_value = rule_col3.text_input(
                            "Value",
                            key=(
                                f"val_"
                                f"{scheme['scheme_id']}"
                            ),
                        )


                        if st.form_submit_button(
                            "Add Rule"
                        ):

                            if field_name and expected_value:

                                result, add_error = (
                                    api_client.admin_add_rule(
                                        scheme["scheme_id"],
                                        field_name,
                                        operator_symbol,
                                        expected_value,
                                    )
                                )

                                if add_error:
                                    st.error(
                                        add_error
                                    )

                                else:
                                    st.rerun()


                    # -------------------------------------
                    # Required Documents
                    # -------------------------------------

                    st.markdown(
                        "**Required Documents**"
                    )

                    for doc in detail.get(
                        "required_documents",
                        [],
                    ):

                        doc_col1, doc_col2 = (
                            st.columns([4, 1])
                        )

                        tag = (
                            "Mandatory"
                            if doc["mandatory"]
                            else "Optional"
                        )

                        doc_col1.write(
                            f"{doc['document_name']} "
                            f"({tag})"
                        )


                        if doc_col2.button(
                            "Delete",
                            key=(
                                f"deldoc_"
                                f"{scheme['scheme_id']}_"
                                f"{doc['document_id']}"
                            ),
                        ):

                            api_client.admin_delete_document(
                                scheme["scheme_id"],
                                doc["document_id"],
                            )

                            st.rerun()


                    with st.form(
                        f"add_doc_form_{scheme['scheme_id']}"
                    ):

                        doc_col1, doc_col2 = (
                            st.columns([3, 1])
                        )

                        document_name = doc_col1.text_input(
                            "Document name",
                            key=(
                                f"docname_"
                                f"{scheme['scheme_id']}"
                            ),
                        )

                        mandatory = doc_col2.checkbox(
                            "Mandatory",
                            value=True,
                            key=(
                                f"mandatory_"
                                f"{scheme['scheme_id']}"
                            ),
                        )


                        if st.form_submit_button(
                            "Add Document"
                        ):

                            if document_name:

                                result, add_error = (
                                    api_client.admin_add_document(
                                        scheme["scheme_id"],
                                        document_name,
                                        mandatory,
                                    )
                                )

                                if add_error:
                                    st.error(
                                        add_error
                                    )

                                else:
                                    st.rerun()