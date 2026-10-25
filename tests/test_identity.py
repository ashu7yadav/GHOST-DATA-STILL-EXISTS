from src.identity import normalize_identifier, resolve_identity


def test_normalize_identifier_handles_case_and_space():
    assert normalize_identifier("  USER@Example.com  ") == "user@example.com"


def test_resolve_identity_uses_historical_email():
    case = {"user_id": 7, "current_email": "user7@example.com", "request_email": "user7@example.com"}
    identities = [{
        "user_id": 7,
        "current_email": "user7@example.com",
        "historical_emails": "old7@example.com; prior7@example.com",
        "phone": "+1-555-1007",
    }]
    audit = [{
        "user_id": 7,
        "old_email": "old7@example.com",
        "new_email": "user7@example.com",
        "event_name": "EMAIL_CHANGED",
    }]
    result = resolve_identity(case, identities, audit)
    assert result["status"] == "resolved"
    assert any("old7@example.com" in str(item) for item in result["historical_matches"])


def test_resolve_identity_rejects_conflicting_match():
    case = {"user_id": 9, "current_email": "other@example.com", "request_email": "other@example.com"}
    identities = [{
        "user_id": 9,
        "current_email": "user9@example.com",
        "historical_emails": "old9@example.com",
        "phone": "+1-555-1009",
    }, {
        "user_id": 12,
        "current_email": "other@example.com",
        "historical_emails": "other-old@example.com",
        "phone": "+1-555-2000",
    }]
    result = resolve_identity(case, identities, [])
    assert result["status"] in {"ambiguous", "conflict"}
