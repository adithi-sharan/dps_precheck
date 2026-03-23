#main ui and logic of app
import streamlit as st

from rules import evaluate_submission, match_record, get_priority
from utils import load_records, save_submission, load_submissions

st.set_page_config(page_title="DMV PreCheck", layout="centered")

st.title("DMV PreCheck")
st.subheader("Pre-verify simple DMV service requests before arrival")
#for the operstor and appicant demo
page = st.sidebar.radio(
    "Navigation",
    ["Applicant Intake", "Operator Dashboard"]
)
if page == "Applicant Intake":
    records = load_records()

    with st.form("precheck_form"):
        st.markdown("### Applicant Request Form")

        full_name = st.text_input("Full Name")
        dob = st.text_input("Date of Birth (YYYY-MM-DD)")
        application_id = st.text_input("Application / License ID")
        current_address = st.text_input("Current Address")
        new_address = st.text_input("New Address")

        request_type = st.selectbox(
            "Request Type",
            ["Address Change", "License Renewal", "Contact Info Update"]
        )

        uploaded_proof = st.checkbox("I am uploading proof / supporting document")
        notes = st.text_area("Optional Notes")

        submitted = st.form_submit_button("Run PreCheck")

    if submitted:
        submission = {
            "full_name": full_name,
            "dob": dob,
            "application_id": application_id,
            "current_address": current_address,
            "new_address": new_address,
            "request_type": request_type,
            "uploaded_proof": uploaded_proof,
            "notes": notes
        }

        matched_record = match_record(submission, records)
        result = evaluate_submission(submission, matched_record)

        submission["status"] = result["status"]
        submission["reasons"] = result["reasons"]
        submission["checks"] = result["checks"]
        submission["priority"] = get_priority(result)

        save_submission(submission)

        st.markdown("---")
        st.markdown("## PreCheck Result")

        status = result["status"]

        if status == "READY_FOR_APPROVAL":
            st.success("READY FOR APPROVAL")
        elif status == "NEEDS_HUMAN_REVIEW":
            st.warning("NEEDS HUMAN REVIEW")
        else:
            st.error("BLOCKED: MISSING INFO")

        st.markdown("### Verification Summary")
        for key, value in result["checks"].items():
            icon = "✅" if value else "⚠️"
            st.write(f"{icon} {key.replace('_', ' ').title()}: {value}")

        st.markdown("### Reasons")
        for reason in result["reasons"]:
            st.write(f"- {reason}")


elif page == "Operator Dashboard":
    st.markdown("## Operator Queue")

    submissions = load_submissions()

    if not submissions:
        st.info("No submissions yet.")
    else:
        total_requests = len(submissions)
        ready_count = sum(1 for s in submissions if s["status"] == "READY_FOR_APPROVAL")
        review_count = sum(1 for s in submissions if s["status"] == "NEEDS_HUMAN_REVIEW")
        blocked_count = sum(1 for s in submissions if s["status"] == "BLOCKED_MISSING_INFO")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Requests", total_requests)
        col2.metric("Ready", ready_count)
        col3.metric("Needs Review", review_count)
        col4.metric("Blocked", blocked_count)

        st.markdown("---")

        priority_order = {"High": 0, "Medium": 1, "Low": 2}
        submissions = sorted(
            submissions,key=lambda x: priority_order.get(x.get("priority", "Low"), 99)
            )
        
        for i, case in enumerate(submissions):
            with st.container():
                st.markdown(f"### {case['full_name']} — {case['request_type']}")
                st.write(f"**Application ID:** {case['application_id']}")
                st.write(f"**Status:** {case['status']}")
                st.write(f"**Priority:** {case.get('priority', 'Low')}")

                if case.get("reasons"):
                    st.write(f"**Top Reason:** {case['reasons'][0]}")

                with st.expander("View Case Details"):
                    st.write(f"**DOB:** {case['dob']}")
                    st.write(f"**Current Address:** {case['current_address']}")
                    st.write(f"**New Address:** {case['new_address']}")
                    st.write(f"**Uploaded Proof:** {case['uploaded_proof']}")
                    st.write(f"**Notes:** {case['notes'] if case['notes'] else 'None'}")

                    st.markdown("#### Verification Checks")
                    for key, value in case.get("checks", {}).items():
                        icon = "✅" if value else "⚠️"
                        st.write(f"{icon} {key.replace('_', ' ').title()}: {value}")

                    st.markdown("#### Reasons")
                    for reason in case["reasons"]:
                        st.write(f"- {reason}")

                    action_col1, action_col2, action_col3 = st.columns(3)
                    action_col1.button("Approve", key=f"approve_{i}")
                    action_col2.button("Escalate", key=f"escalate_{i}")
                    action_col3.button("Request Info", key=f"request_{i}")

                st.markdown("---")