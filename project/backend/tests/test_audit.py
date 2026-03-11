"""
Tests for audit log retrieval endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json
import io

from app.main import app
from app.models.user import User, UserRole
from app.models.audit_chain import AuditChain
from app.core.security import create_access_token


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def admin_token(db_session: Session):
    """Create admin user and return JWT token"""
    admin = User(
        name="Admin User",
        email="admin@test.com",
        password_hash="hashed_password",
        role=UserRole.ADMIN
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    
    token_data = {
        "user_id": admin.id,
        "email": admin.email,
        "role": admin.role.value
    }
    return create_access_token(data=token_data)


@pytest.fixture
def doctor_token(db_session: Session):
    """Create doctor user and return JWT token"""
    doctor = User(
        name="Doctor User",
        email="doctor@test.com",
        password_hash="hashed_password",
        role=UserRole.DOCTOR
    )
    db_session.add(doctor)
    db_session.commit()
    db_session.refresh(doctor)
    
    token_data = {
        "user_id": doctor.id,
        "email": doctor.email,
        "role": doctor.role.value
    }
    return create_access_token(data=token_data)


@pytest.fixture
def sample_audit_logs(db_session: Session):
    """Create sample audit log entries"""
    # Create users
    user1 = User(
        name="User One",
        email="user1@test.com",
        password_hash="hashed",
        role=UserRole.DOCTOR
    )
    user2 = User(
        name="User Two",
        email="user2@test.com",
        password_hash="hashed",
        role=UserRole.NURSE
    )
    db_session.add_all([user1, user2])
    db_session.commit()
    
    # Create audit entries with different timestamps and types
    base_time = datetime.utcnow()
    
    audit_entries = [
        AuditChain(
            record_id=1,
            record_type="medical_record",
            record_data={"diagnosis": "Flu", "notes": "Patient has fever"},
            hash="hash1",
            previous_hash="0",
            timestamp=base_time - timedelta(days=5),
            user_id=user1.id,
            is_tampered=False
        ),
        AuditChain(
            record_id=2,
            record_type="medical_record",
            record_data={"diagnosis": "Cold", "notes": "Mild symptoms"},
            hash="hash2",
            previous_hash="hash1",
            timestamp=base_time - timedelta(days=4),
            user_id=user1.id,
            is_tampered=False
        ),
        AuditChain(
            record_id=1,
            record_type="appointment",
            record_data={"status": "scheduled", "time": "2024-01-15T10:00:00"},
            hash="hash3",
            previous_hash="hash2",
            timestamp=base_time - timedelta(days=3),
            user_id=user2.id,
            is_tampered=False
        ),
        AuditChain(
            record_id=3,
            record_type="medical_record",
            record_data={"diagnosis": "Diabetes", "notes": "Regular checkup"},
            hash="hash4",
            previous_hash="hash3",
            timestamp=base_time - timedelta(days=2),
            user_id=user1.id,
            is_tampered=True
        ),
        AuditChain(
            record_id=2,
            record_type="appointment",
            record_data={"status": "completed", "time": "2024-01-16T14:00:00"},
            hash="hash5",
            previous_hash="hash4",
            timestamp=base_time - timedelta(days=1),
            user_id=user2.id,
            is_tampered=False
        ),
    ]
    
    db_session.add_all(audit_entries)
    db_session.commit()
    
    return {
        "user1_id": user1.id,
        "user2_id": user2.id,
        "entries": audit_entries
    }


class TestAuditLogRetrieval:
    """Test audit log retrieval endpoint"""
    
    def test_get_audit_logs_requires_authentication(self, client):
        """Test that audit logs endpoint requires authentication"""
        response = client.get("/api/v1/audit/logs")
        assert response.status_code == 401  # No auth header
    
    def test_get_audit_logs_requires_admin_role(self, client, doctor_token):
        """Test that audit logs endpoint requires admin role"""
        headers = {"Authorization": f"Bearer {doctor_token}"}
        response = client.get("/api/v1/audit/logs", headers=headers)
        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]
    
    def test_get_all_audit_logs(self, client, admin_token, sample_audit_logs):
        """Test retrieving all audit logs without filters"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/audit/logs", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert data["total_pages"] == 1
        assert len(data["logs"]) == 5
        
        # Verify logs are ordered by timestamp (newest first)
        timestamps = [log["timestamp"] for log in data["logs"]]
        assert timestamps == sorted(timestamps, reverse=True)
    
    def test_get_audit_logs_with_date_range_filter(self, client, admin_token, sample_audit_logs):
        """Test filtering audit logs by date range"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Filter for entries older than 3.5 days (should get 2 entries: 5 days and 4 days old)
        start_date = (datetime.utcnow() - timedelta(days=5, hours=1)).isoformat()
        end_date = (datetime.utcnow() - timedelta(days=3, hours=12)).isoformat()
        
        response = client.get(
            f"/api/v1/audit/logs?start_date={start_date}&end_date={end_date}",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should get 2 entries (5 days and 4 days old)
        assert data["total"] == 2
        assert len(data["logs"]) == 2
    
    def test_get_audit_logs_with_user_filter(self, client, admin_token, sample_audit_logs):
        """Test filtering audit logs by user ID"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        user1_id = sample_audit_logs["user1_id"]
        
        response = client.get(
            f"/api/v1/audit/logs?user_id={user1_id}",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # User1 has 3 entries
        assert data["total"] == 3
        assert len(data["logs"]) == 3
        
        # Verify all logs belong to user1
        for log in data["logs"]:
            assert log["user_id"] == user1_id
    
    def test_get_audit_logs_with_record_type_filter(self, client, admin_token, sample_audit_logs):
        """Test filtering audit logs by record type"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = client.get(
            "/api/v1/audit/logs?record_type=medical_record",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should get 3 medical_record entries
        assert data["total"] == 3
        assert len(data["logs"]) == 3
        
        # Verify all logs are medical_record type
        for log in data["logs"]:
            assert log["record_type"] == "medical_record"
    
    def test_get_audit_logs_with_multiple_filters(self, client, admin_token, sample_audit_logs):
        """Test filtering audit logs with multiple filters"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        user2_id = sample_audit_logs["user2_id"]
        
        response = client.get(
            f"/api/v1/audit/logs?user_id={user2_id}&record_type=appointment",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # User2 has 2 appointment entries
        assert data["total"] == 2
        assert len(data["logs"]) == 2
        
        # Verify filters are applied
        for log in data["logs"]:
            assert log["user_id"] == user2_id
            assert log["record_type"] == "appointment"
    
    def test_get_audit_logs_pagination(self, client, admin_token, sample_audit_logs):
        """Test pagination of audit logs"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get first page with 2 items
        response = client.get(
            "/api/v1/audit/logs?page=1&page_size=2",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["total_pages"] == 3
        assert len(data["logs"]) == 2
        
        # Get second page
        response = client.get(
            "/api/v1/audit/logs?page=2&page_size=2",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["page"] == 2
        assert len(data["logs"]) == 2
        
        # Get last page
        response = client.get(
            "/api/v1/audit/logs?page=3&page_size=2",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["page"] == 3
        assert len(data["logs"]) == 1  # Only 1 item on last page
    
    def test_get_audit_logs_includes_user_info(self, client, admin_token, sample_audit_logs):
        """Test that audit logs include user name and email"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = client.get("/api/v1/audit/logs", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify user info is included
        for log in data["logs"]:
            if log["user_id"] is not None:
                assert log["user_name"] is not None
                assert log["user_email"] is not None
    
    def test_get_audit_logs_empty_result(self, client, admin_token, sample_audit_logs):
        """Test audit logs with filters that return no results"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Filter for non-existent user
        response = client.get(
            "/api/v1/audit/logs?user_id=99999",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 0
        assert data["total_pages"] == 0
        assert len(data["logs"]) == 0
    
    def test_get_audit_logs_invalid_page(self, client, admin_token, sample_audit_logs):
        """Test audit logs with invalid page number"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Page must be >= 1
        response = client.get(
            "/api/v1/audit/logs?page=0",
            headers=headers
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_get_audit_logs_invalid_page_size(self, client, admin_token, sample_audit_logs):
        """Test audit logs with invalid page size"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Page size must be <= 100
        response = client.get(
            "/api/v1/audit/logs?page_size=101",
            headers=headers
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_get_audit_logs_shows_tampered_flag(self, client, admin_token, sample_audit_logs):
        """Test that audit logs show tampered flag"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = client.get("/api/v1/audit/logs", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Find the tampered entry
        tampered_logs = [log for log in data["logs"] if log["is_tampered"]]
        assert len(tampered_logs) == 1
        assert tampered_logs[0]["record_id"] == 3
        assert tampered_logs[0]["record_type"] == "medical_record"



class TestTamperingAlertRetrieval:
    """Test tampering alert retrieval endpoint"""
    
    def test_get_tampering_alerts_requires_authentication(self, client):
        """Test that tampering alerts endpoint requires authentication"""
        response = client.get("/api/v1/audit/tampering-alerts")
        assert response.status_code == 401  # No auth header
    
    def test_get_tampering_alerts_requires_admin_role(self, client, doctor_token):
        """Test that tampering alerts endpoint requires admin role"""
        headers = {"Authorization": f"Bearer {doctor_token}"}
        response = client.get("/api/v1/audit/tampering-alerts", headers=headers)
        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]
    
    def test_get_tampering_alerts_empty_when_no_tampering(self, client, admin_token, db_session):
        """Test that tampering alerts returns empty list when no tampering detected"""
        # Create audit entries without tampering
        user = User(
            name="Test User",
            email="test@test.com",
            password_hash="hashed",
            role=UserRole.DOCTOR
        )
        db_session.add(user)
        db_session.commit()
        
        audit_entry = AuditChain(
            record_id=1,
            record_type="medical_record",
            record_data={"diagnosis": "Flu"},
            hash="hash1",
            previous_hash="0",
            timestamp=datetime.utcnow(),
            user_id=user.id,
            is_tampered=False
        )
        db_session.add(audit_entry)
        db_session.commit()
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/audit/tampering-alerts", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0
    
    def test_get_tampering_alerts_returns_flagged_records(self, client, admin_token, sample_audit_logs):
        """Test that tampering alerts returns only flagged records"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/audit/tampering-alerts", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return only the 1 tampered entry from sample data
        assert len(data) == 1
        
        # Verify it's the correct tampered entry
        alert = data[0]
        assert alert["record_id"] == 3
        assert alert["record_type"] == "medical_record"
    
    def test_get_tampering_alerts_includes_record_details(self, client, admin_token, sample_audit_logs):
        """Test that tampering alerts include all required details"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/audit/tampering-alerts", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1
        alert = data[0]
        
        # Verify all required fields are present
        assert "id" in alert
        assert "record_id" in alert
        assert "record_type" in alert
        assert "hash" in alert
        assert "timestamp" in alert
        assert "user_id" in alert
        assert "user_name" in alert
        assert "user_email" in alert
        
        # Verify values
        assert alert["record_id"] == 3
        assert alert["record_type"] == "medical_record"
        assert alert["hash"] == "hash4"
        assert alert["user_name"] == "User One"
        assert alert["user_email"] == "user1@test.com"
    
    def test_get_tampering_alerts_sorted_by_timestamp_default(self, client, admin_token, db_session):
        """Test that tampering alerts are sorted by timestamp (newest first) by default"""
        # Create user
        user = User(
            name="Test User",
            email="test@test.com",
            password_hash="hashed",
            role=UserRole.DOCTOR
        )
        db_session.add(user)
        db_session.commit()
        
        # Create multiple tampered entries with different timestamps
        base_time = datetime.utcnow()
        tampered_entries = [
            AuditChain(
                record_id=1,
                record_type="medical_record",
                record_data={"diagnosis": "Flu"},
                hash="hash1",
                previous_hash="0",
                timestamp=base_time - timedelta(days=3),
                user_id=user.id,
                is_tampered=True
            ),
            AuditChain(
                record_id=2,
                record_type="appointment",
                record_data={"status": "scheduled"},
                hash="hash2",
                previous_hash="hash1",
                timestamp=base_time - timedelta(days=1),
                user_id=user.id,
                is_tampered=True
            ),
            AuditChain(
                record_id=3,
                record_type="medical_record",
                record_data={"diagnosis": "Cold"},
                hash="hash3",
                previous_hash="hash2",
                timestamp=base_time - timedelta(days=2),
                user_id=user.id,
                is_tampered=True
            ),
        ]
        db_session.add_all(tampered_entries)
        db_session.commit()
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/audit/tampering-alerts", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 3
        
        # Verify sorted by timestamp (newest first)
        timestamps = [alert["timestamp"] for alert in data]
        assert timestamps == sorted(timestamps, reverse=True)
        
        # Verify order: record_id 2 (1 day ago), 3 (2 days ago), 1 (3 days ago)
        assert data[0]["record_id"] == 2
        assert data[1]["record_id"] == 3
        assert data[2]["record_id"] == 1
    
    def test_get_tampering_alerts_sorted_by_severity(self, client, admin_token, db_session):
        """Test that tampering alerts can be sorted by severity (medical_record first)"""
        # Create user
        user = User(
            name="Test User",
            email="test@test.com",
            password_hash="hashed",
            role=UserRole.DOCTOR
        )
        db_session.add(user)
        db_session.commit()
        
        # Create tampered entries with different record types
        base_time = datetime.utcnow()
        tampered_entries = [
            AuditChain(
                record_id=1,
                record_type="appointment",
                record_data={"status": "scheduled"},
                hash="hash1",
                previous_hash="0",
                timestamp=base_time - timedelta(days=1),
                user_id=user.id,
                is_tampered=True
            ),
            AuditChain(
                record_id=2,
                record_type="medical_record",
                record_data={"diagnosis": "Flu"},
                hash="hash2",
                previous_hash="hash1",
                timestamp=base_time - timedelta(days=3),
                user_id=user.id,
                is_tampered=True
            ),
            AuditChain(
                record_id=3,
                record_type="medical_record",
                record_data={"diagnosis": "Cold"},
                hash="hash3",
                previous_hash="hash2",
                timestamp=base_time - timedelta(days=2),
                user_id=user.id,
                is_tampered=True
            ),
        ]
        db_session.add_all(tampered_entries)
        db_session.commit()
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/audit/tampering-alerts?sort_by=severity", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 3
        
        # Verify medical_record entries come first
        assert data[0]["record_type"] == "medical_record"
        assert data[1]["record_type"] == "medical_record"
        assert data[2]["record_type"] == "appointment"
        
        # Within medical_record type, should be sorted by timestamp (newest first)
        # record_id 3 (2 days ago) should come before record_id 2 (3 days ago)
        assert data[0]["record_id"] == 3
        assert data[1]["record_id"] == 2
        assert data[2]["record_id"] == 1
    
    def test_get_tampering_alerts_with_null_user(self, client, admin_token, db_session):
        """Test that tampering alerts handle entries with null user_id"""
        # Create tampered entry without user
        tampered_entry = AuditChain(
            record_id=1,
            record_type="medical_record",
            record_data={"diagnosis": "Flu"},
            hash="hash1",
            previous_hash="0",
            timestamp=datetime.utcnow(),
            user_id=None,
            is_tampered=True
        )
        db_session.add(tampered_entry)
        db_session.commit()
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/audit/tampering-alerts", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1
        alert = data[0]
        
        # Verify null user is handled gracefully
        assert alert["user_id"] is None
        assert alert["user_name"] is None
        assert alert["user_email"] is None
    
    def test_get_tampering_alerts_multiple_records(self, client, admin_token, db_session):
        """Test retrieving multiple tampering alerts"""
        # Create user
        user = User(
            name="Test User",
            email="test@test.com",
            password_hash="hashed",
            role=UserRole.DOCTOR
        )
        db_session.add(user)
        db_session.commit()
        
        # Create 5 tampered entries
        base_time = datetime.utcnow()
        tampered_entries = []
        for i in range(5):
            entry = AuditChain(
                record_id=i + 1,
                record_type="medical_record" if i % 2 == 0 else "appointment",
                record_data={"data": f"record_{i}"},
                hash=f"hash{i}",
                previous_hash=f"hash{i-1}" if i > 0 else "0",
                timestamp=base_time - timedelta(days=i),
                user_id=user.id,
                is_tampered=True
            )
            tampered_entries.append(entry)
        
        db_session.add_all(tampered_entries)
        db_session.commit()
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/audit/tampering-alerts", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 5
        
        # Verify all are tampered records
        for alert in data:
            assert alert["record_id"] in [1, 2, 3, 4, 5]


class TestAuditLogExport:
    """Test audit log export endpoint"""
    
    def test_export_audit_logs_requires_authentication(self, client):
        """Test that export endpoint requires authentication"""
        response = client.get("/api/v1/audit/export")
        assert response.status_code == 401  # No auth header
    
    def test_export_audit_logs_requires_admin_role(self, client, doctor_token):
        """Test that export endpoint requires admin role"""
        headers = {"Authorization": f"Bearer {doctor_token}"}
        response = client.get("/api/v1/audit/export", headers=headers)
        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]
    
    def test_export_audit_logs_json_format(self, client, admin_token, sample_audit_logs):
        """Test exporting audit logs in JSON format"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/audit/export?format=json", headers=headers)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        assert "attachment" in response.headers["content-disposition"]
        assert "audit_logs_" in response.headers["content-disposition"]
        assert ".json" in response.headers["content-disposition"]
        
        # Parse JSON content
        data = json.loads(response.content)
        
        # Verify all 5 entries are exported
        assert len(data) == 5
        
        # Verify structure of first entry
        first_entry = data[0]
        assert "id" in first_entry
        assert "record_id" in first_entry
        assert "record_type" in first_entry
        assert "record_data" in first_entry
        assert "hash" in first_entry
        assert "previous_hash" in first_entry
        assert "timestamp" in first_entry
        assert "user_id" in first_entry
        assert "is_tampered" in first_entry
        assert "user_name" in first_entry
        assert "user_email" in first_entry
    
    def test_export_audit_logs_csv_format(self, client, admin_token, sample_audit_logs):
        """Test exporting audit logs in CSV format"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/audit/export?format=csv", headers=headers)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]
        assert "audit_logs_" in response.headers["content-disposition"]
        assert ".csv" in response.headers["content-disposition"]
        
        # Parse CSV content
        csv_content = response.content.decode()
        lines = csv_content.strip().split('\n')
        
        # Verify header + 5 data rows
        assert len(lines) == 6  # 1 header + 5 data rows
        
        # Verify header
        header = lines[0]
        assert "id" in header
        assert "record_id" in header
        assert "record_type" in header
        assert "hash" in header
        assert "timestamp" in header
        assert "user_id" in header
        assert "is_tampered" in header
    
    def test_export_audit_logs_default_format_is_json(self, client, admin_token, sample_audit_logs):
        """Test that default export format is JSON"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/audit/export", headers=headers)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        assert ".json" in response.headers["content-disposition"]
    
    def test_export_audit_logs_invalid_format(self, client, admin_token, sample_audit_logs):
        """Test that invalid format returns error"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/audit/export?format=xml", headers=headers)
        
        assert response.status_code == 400
        assert "Invalid format" in response.json()["detail"]
    
    def test_export_audit_logs_with_date_filter(self, client, admin_token, sample_audit_logs):
        """Test exporting audit logs with date range filter"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Filter for entries older than 3.5 days (should get 2 entries)
        start_date = (datetime.utcnow() - timedelta(days=5, hours=1)).isoformat()
        end_date = (datetime.utcnow() - timedelta(days=3, hours=12)).isoformat()
        
        response = client.get(
            f"/api/v1/audit/export?format=json&start_date={start_date}&end_date={end_date}",
            headers=headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.content)
        
        # Should get 2 entries (5 days and 4 days old)
        assert len(data) == 2
    
    def test_export_audit_logs_with_user_filter(self, client, admin_token, sample_audit_logs):
        """Test exporting audit logs with user filter"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        user1_id = sample_audit_logs["user1_id"]
        
        response = client.get(
            f"/api/v1/audit/export?format=json&user_id={user1_id}",
            headers=headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.content)
        
        # User1 has 3 entries
        assert len(data) == 3
        
        # Verify all logs belong to user1
        for log in data:
            assert log["user_id"] == user1_id
    
    def test_export_audit_logs_with_record_type_filter(self, client, admin_token, sample_audit_logs):
        """Test exporting audit logs with record type filter"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = client.get(
            "/api/v1/audit/export?format=json&record_type=medical_record",
            headers=headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.content)
        
        # Should get 3 medical_record entries
        assert len(data) == 3
        
        # Verify all logs are medical_record type
        for log in data:
            assert log["record_type"] == "medical_record"
    
    def test_export_audit_logs_with_multiple_filters(self, client, admin_token, sample_audit_logs):
        """Test exporting audit logs with multiple filters"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        user2_id = sample_audit_logs["user2_id"]
        
        response = client.get(
            f"/api/v1/audit/export?format=json&user_id={user2_id}&record_type=appointment",
            headers=headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.content)
        
        # User2 has 2 appointment entries
        assert len(data) == 2
        
        # Verify filters are applied
        for log in data:
            assert log["user_id"] == user2_id
            assert log["record_type"] == "appointment"
    
    def test_export_audit_logs_csv_includes_all_fields(self, client, admin_token, sample_audit_logs):
        """Test that CSV export includes all relevant fields"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/audit/export?format=csv", headers=headers)
        
        assert response.status_code == 200
        
        # Parse CSV
        csv_content = response.content.decode()
        lines = csv_content.strip().split('\n')
        
        # Check header has all required fields
        header_line = lines[0].replace('\r', '')  # Remove carriage return
        header = header_line.split(',')
        required_fields = [
            "id", "record_id", "record_type", "record_data", "hash",
            "previous_hash", "timestamp", "user_id", "user_name",
            "user_email", "is_tampered"
        ]
        
        for field in required_fields:
            assert field in header
    
    def test_export_audit_logs_json_includes_record_data(self, client, admin_token, sample_audit_logs):
        """Test that JSON export includes full record_data"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/audit/export?format=json", headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.content)
        
        # Find a medical_record entry
        medical_records = [log for log in data if log["record_type"] == "medical_record"]
        assert len(medical_records) > 0
        
        # Verify record_data is a dict with expected fields
        record = medical_records[0]
        assert isinstance(record["record_data"], dict)
        assert "diagnosis" in record["record_data"]
    
    def test_export_audit_logs_csv_serializes_record_data(self, client, admin_token, sample_audit_logs):
        """Test that CSV export properly serializes record_data as JSON string"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/audit/export?format=csv", headers=headers)
        
        assert response.status_code == 200
        
        # Parse CSV
        import csv
        csv_content = response.content.decode()
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)
        
        # Verify record_data can be parsed as JSON
        for row in rows:
            record_data = json.loads(row["record_data"])
            assert isinstance(record_data, dict)
    
    def test_export_audit_logs_empty_result(self, client, admin_token, sample_audit_logs):
        """Test exporting audit logs with filters that return no results"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Filter for non-existent user
        response = client.get(
            "/api/v1/audit/export?format=json&user_id=99999",
            headers=headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.content)
        
        assert len(data) == 0
    
    def test_export_audit_logs_includes_tampered_flag(self, client, admin_token, sample_audit_logs):
        """Test that export includes tampered flag"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/audit/export?format=json", headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.content)
        
        # Find the tampered entry
        tampered_logs = [log for log in data if log["is_tampered"]]
        assert len(tampered_logs) == 1
        assert tampered_logs[0]["record_id"] == 3
        assert tampered_logs[0]["record_type"] == "medical_record"
    
    def test_export_audit_logs_ordered_by_timestamp(self, client, admin_token, sample_audit_logs):
        """Test that exported logs are ordered by timestamp (newest first)"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/audit/export?format=json", headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.content)
        
        # Verify logs are ordered by timestamp (newest first)
        timestamps = [log["timestamp"] for log in data]
        assert timestamps == sorted(timestamps, reverse=True)
    
    def test_export_audit_logs_includes_user_info(self, client, admin_token, sample_audit_logs):
        """Test that export includes user name and email"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/audit/export?format=json", headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.content)
        
        # Verify user info is included
        for log in data:
            if log["user_id"] is not None:
                assert log["user_name"] is not None
                assert log["user_email"] is not None
    
    def test_export_audit_logs_handles_null_user(self, client, admin_token, db_session):
        """Test that export handles entries with null user_id"""
        # Create audit entry without user
        audit_entry = AuditChain(
            record_id=1,
            record_type="medical_record",
            record_data={"diagnosis": "Flu"},
            hash="hash1",
            previous_hash="0",
            timestamp=datetime.utcnow(),
            user_id=None,
            is_tampered=False
        )
        db_session.add(audit_entry)
        db_session.commit()
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/audit/export?format=json", headers=headers)
        
        assert response.status_code == 200
        data = json.loads(response.content)
        
        # Find entry with null user
        null_user_logs = [log for log in data if log["user_id"] is None]
        assert len(null_user_logs) == 1
        assert null_user_logs[0]["user_name"] is None
        assert null_user_logs[0]["user_email"] is None
    
    def test_export_audit_logs_csv_handles_null_user(self, client, admin_token, db_session):
        """Test that CSV export handles entries with null user_id"""
        # Create audit entry without user
        audit_entry = AuditChain(
            record_id=1,
            record_type="medical_record",
            record_data={"diagnosis": "Flu"},
            hash="hash1",
            previous_hash="0",
            timestamp=datetime.utcnow(),
            user_id=None,
            is_tampered=False
        )
        db_session.add(audit_entry)
        db_session.commit()
        
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = client.get("/api/v1/audit/export?format=csv", headers=headers)
        
        assert response.status_code == 200
        
        # Parse CSV
        import csv
        csv_content = response.content.decode()
        reader = csv.DictReader(io.StringIO(csv_content))
        rows = list(reader)
        
        # Find entry with empty user fields
        null_user_rows = [row for row in rows if row["user_id"] == ""]
        assert len(null_user_rows) == 1
        assert null_user_rows[0]["user_name"] == ""
        assert null_user_rows[0]["user_email"] == ""
