# a file storing rules to be classified in one of the three different apporvals 

import re


VALID_REQUEST_TYPES = {
    "Address Change",
    "License Renewal",
    "Contact Info Update"
}

def normalize_text(value: str) -> str:
    return value.strip().lower() if value else ""


def is_address_valid(address: str) -> bool:
    if not address or len(address.strip()) < 10:
        return False
    return bool(re.search(r"\d", address))

def validate_required_fields(submission: dict) -> list[str]:
    missing = []

    required_fields = [
        "full_name",
        "dob",
        "application_id",
        "current_address",
        "new_address",
        "request_type"
    ]

    for field in required_fields:
        if not submission.get(field):
            missing.append(field)

    return missing

def match_record(submission: dict, records: list[dict]) -> dict | None:
    application_id = normalize_text(submission.get("application_id"))

    for record in records:
        if normalize_text(record.get("application_id")) == application_id:
            return record

    return None

def evaluate_submission(submission: dict, record: dict | None) -> dict:
    reasons = []
    checks = {}

    missing_fields = validate_required_fields(submission)
    if missing_fields:
        return {
            "status": "BLOCKED_MISSING_INFO",
            "checks": {
                "required_fields_complete": False
            },
            "reasons": [f"Missing required fields: {', '.join(missing_fields)}"]
        }

    checks["request_type_valid"] = submission["request_type"] in VALID_REQUEST_TYPES
    if not checks["request_type_valid"]:
        return {
            "status": "BLOCKED_MISSING_INFO",
            "checks": checks,
            "reasons": ["Request type is not eligible for precheck."]
        }

    checks["new_address_valid"] = is_address_valid(submission["new_address"])
    if not checks["new_address_valid"]:
        return {
            "status": "BLOCKED_MISSING_INFO",
            "checks": checks,
            "reasons": ["New address format appears invalid."]
        }

    checks["record_found"] = record is not None
    if not checks["record_found"]:
        return {
            "status": "BLOCKED_MISSING_INFO",
            "checks": checks,
            "reasons": ["No matching DMV record found."]
        }

    checks["full_name_match"] = (
        normalize_text(submission["full_name"]) == normalize_text(record["full_name"])
    )
    checks["dob_match"] = (
        normalize_text(submission["dob"]) == normalize_text(record["dob"])
    )
    checks["current_address_match"] = (
        normalize_text(submission["current_address"]) == normalize_text(record["current_address"])
    )

    proof_available = submission.get("uploaded_proof", False) or record.get("document_on_file", False)
    checks["proof_available"] = proof_available

    checks["license_active"] = record.get("license_status") == "active"

    if not proof_available:
        return {
            "status": "BLOCKED_MISSING_INFO",
            "checks": checks,
            "reasons": ["No supporting proof available and no document is on file."]
        }

    review_reasons = []

    if not checks["full_name_match"]:
        review_reasons.append("Submitted name does not exactly match DMV record.")
    if not checks["dob_match"]:
        review_reasons.append("Date of birth does not match DMV record.")
    if not checks["current_address_match"]:
        review_reasons.append("Current address does not match record.")
    if not checks["license_active"]:
        review_reasons.append("License status requires human review.")

    if review_reasons:
        return {
            "status": "NEEDS_HUMAN_REVIEW",
            "checks": checks,
            "reasons": review_reasons
        }

    return {
        "status": "READY_FOR_APPROVAL",
        "checks": checks,
        "reasons": ["All verification checks passed."]
    }
