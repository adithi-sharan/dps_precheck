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

    # info required for everyone
    common_fields = [
        "full_name",
        "dob",
        "application_id",
        "request_type"
    ]

    for field in common_fields:
        if not submission.get(field):
            missing.append(field)

    request_type = submission.get("request_type")

    if request_type == "Address Change":
        address_fields = ["current_address", "new_address"]
        for field in address_fields:
            if not submission.get(field):
                missing.append(field)

    elif request_type == "License Renewal":
        renewal_fields = ["current_address"]
        for field in renewal_fields:
            if not submission.get(field):
                missing.append(field)

        if submission.get("vision_attestation") is not True:
            missing.append("vision_attestation")

        if submission.get("renewal_eligible") is not True:
            missing.append("renewal_eligible")

    elif request_type == "Contact Info Update":
        has_new_email = bool(submission.get("new_email"))
        has_new_phone = bool(submission.get("new_phone"))

        if not has_new_email and not has_new_phone:
            missing.append("new_email_or_new_phone")

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

    checks["license_active"] = record.get("license_status") == "active"

    request_type = submission["request_type"]

    if request_type == "Address Change":
        checks["current_address_match"] = (
            normalize_text(submission["current_address"]) == normalize_text(record["current_address"])
        )
        checks["new_address_valid"] = is_address_valid(submission["new_address"])

        proof_available = submission.get("uploaded_proof", False) or record.get("document_on_file", False)
        checks["proof_available"] = proof_available

        if not checks["new_address_valid"]:
            return {
                "status": "BLOCKED_MISSING_INFO",
                "checks": checks,
                "reasons": ["New address format appears invalid."]
            }

        if not proof_available:
            return {
                "status": "BLOCKED_MISSING_INFO",
                "checks": checks,
                "reasons": ["No supporting proof available and no document is on file."]
            }

    elif request_type == "License Renewal":
        checks["current_address_match"] = (
            normalize_text(submission["current_address"]) == normalize_text(record["current_address"])
        )
        checks["vision_attestation_complete"] = submission.get("vision_attestation", False)
        checks["renewal_eligible_confirmed"] = submission.get("renewal_eligible", False)

    elif request_type == "Contact Info Update":
        checks["contact_update_provided"] = bool(submission.get("new_email")) or bool(submission.get("new_phone"))

    review_reasons = []

    if not checks["full_name_match"]:
        review_reasons.append("Submitted name does not exactly match DMV record.")
    if not checks["dob_match"]:
        review_reasons.append("Date of birth does not match DMV record.")
    if not checks["license_active"]:
        review_reasons.append("License status requires human review.")

    if request_type in {"Address Change", "License Renewal"}:
        if not checks.get("current_address_match", True):
            review_reasons.append("Current address does not match record.")

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


def get_priority(result: dict) -> str:
    status = result["status"]

    if status == "READY_FOR_APPROVAL":
        return "High"
    if status == "NEEDS_HUMAN_REVIEW":
        return "Medium"
    return "Low"