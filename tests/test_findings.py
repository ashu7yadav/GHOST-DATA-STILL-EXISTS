from src.findings import find_checks


def test_find_checks_flags_active_record_and_sync_risk():
    case = {
        "case_id": "case_101",
        "user_id": 101,
        "request_email": "user101@example.com",
        "current_email": "user101@example.com",
        "deletion_requested": True,
        "authorized_for_deletion": True,
        "audit_at": "2024-01-02T01:00:00",
    }
    identifiers = [{
        "user_id": 101,
        "current_email": "user101@example.com",
        "historical_emails": "old101@example.com",
        "phone": "+1-555-1101",
    }]
    data = {
        "evidence_files": [{
            "case_id": "case_101",
            "evidence_id": "evidence_101",
            "system_id": "account_service",
            "resource_id": "account_101",
            "state": "PRESENT",
            "event_time": "2024-01-02T00:00:00",
        }],
        "system_activity": [{
            "case_id": "case_101",
            "system_id": "sync_service",
            "resource_id": "sync_101",
            "event_name": "SYNC_ACTIVE",
            "event_time": "2024-01-01T23:00:00",
            "outcome": "ACTIVE",
        }],
        "deletion_rules": [{"category": "profile", "required_action": "DELETE", "retention": "not required"}],
    }
    findings = find_checks(case, identifiers, data)
    assert any(item["type"] == "remaining_record" for item in findings)
    assert any(item["type"] == "active_data_flow" for item in findings)


def test_find_checks_handles_not_applicable_case():
    case = {"case_id": "case_999", "deletion_requested": False, "authorized_for_deletion": False, "request_type": "NO_DELETION"}
    findings = find_checks(case, [], {"evidence_files": [], "system_activity": [], "deletion_rules": []})
    assert findings == []
