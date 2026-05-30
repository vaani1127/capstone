# Blockchain Audit System

HealthSaathi uses a hash-linked audit chain to provide tamper-evident logging of all
clinical and scheduling actions. This document describes the design, API, and
verification workflow.

## Concept

Every write operation that affects patient data appends a new block to the audit chain.
Each block contains a SHA-256 hash of its own data combined with the hash of the previous
block. A break anywhere in the chain (a changed hash) proves that a record was tampered with
after creation.

```
Genesis Block                  Block 2                      Block 3
┌────────────────────┐         ┌────────────────────┐       ┌────────────────────┐
│ record_id: 1       │         │ record_id: 42       │       │ record_id: 42      │
│ record_type: ...   │         │ record_type: ...    │       │ record_type: ...   │
│ record_data: {...} │  hash   │ record_data: {...}  │ hash  │ record_data: {...} │
│ previous_hash: "0" │ ──────► │ previous_hash: H1  │ ────► │ previous_hash: H2  │
│ hash: H1           │         │ hash: H2            │       │ hash: H3           │
└────────────────────┘         └────────────────────┘       └────────────────────┘
```

If `record_data` in Block 2 is modified after creation, recomputing its hash gives a
different value — which will not match Block 3's `previous_hash`. The chain is broken.

## Database Table: `audit_chain`

| Column | Type | Description |
|--------|------|-------------|
| `id` | integer PK | Auto-increment block number |
| `record_id` | integer | ID of the affected entity |
| `record_type` | varchar | Entity type (see table below) |
| `record_data` | JSON | Snapshot of relevant fields at time of action |
| `hash` | varchar(64) | SHA-256 of `record_id + record_type + record_data + previous_hash` |
| `previous_hash` | varchar(64) | Hash of the previous block (`"0"` for genesis) |
| `timestamp` | datetime | UTC timestamp of block creation |
| `created_by` | integer FK → users | User who triggered the action |
| `is_tampered` | boolean | Set to `true` when a verification check detects a mismatch |

## Record Types

| `record_type` | Triggered by |
|--------------|--------------|
| `medical_record` | Medical record created or updated |
| `appointment_created` | Patient books an appointment |
| `appointment_cancelled` | Appointment cancelled |
| `appointment_rescheduled` | Appointment rescheduled to a new time |
| `appointment_status_updated` | Doctor/nurse changes appointment status |
| `walk_in_registered` | Staff registers a walk-in patient |

## Service API (`app/services/blockchain_service.py`)

### `generate_hash(record_id, record_type, record_data, previous_hash) → str`

Computes and returns the SHA-256 hex digest for a block. Deterministic for the same inputs.

### `create_audit_entry(db, record_id, record_type, record_data, user_id) → AuditChain`

Appends a new block to the chain. Fetches the latest block's hash as `previous_hash`
(or `"0"` if the chain is empty), computes the new hash, inserts the row, and **flushes**
(does not commit — the caller's outer transaction commits everything atomically).

```python
from app.services.blockchain_service import create_audit_entry

# Inside a service method, after db.flush() on the primary entity:
create_audit_entry(
    db,
    record_id=appointment.id,
    record_type="appointment_created",
    record_data={
        "patient_id": appointment.patient_id,
        "doctor_id": appointment.doctor_id,
        "scheduled_time": appointment.scheduled_time.isoformat(),
    },
    user_id=current_user.id,
)
db.commit()   # commits both the appointment row and the audit entry
```

### `create_medical_record_audit_entry(db, medical_record, user_id) → AuditChain`

Convenience wrapper for medical record callers. Extracts `record_data` from the model
and delegates to `create_audit_entry` with `record_type="medical_record"`.

### `verify_record_integrity(db, audit_entry_id) → bool`

Fetches the audit chain entry by `id`, recomputes its hash, and compares to the stored hash.
Returns `True` if they match, `False` if they differ.
Raises `ValueError` if no entry exists for the given ID.

### `flag_tampered_record(db, audit_entry_id) → None`

Sets `is_tampered = True` on the entry and commits. Called automatically by the
`POST /audit/verify/{id}` endpoint when integrity check fails.

### `verify_chain_integrity(db) → dict`

Walks every block in order (ascending `id`) and verifies:
1. Each block's `hash` matches a fresh computation of its fields.
2. Each block's `previous_hash` matches the prior block's `hash`.

Returns:
```python
{
    "is_valid": bool,
    "total_blocks": int,
    "invalid_blocks": [{"id": int, "reason": str}, ...],
    "message": str,
}
```

## REST API

All audit endpoints require Admin role.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/audit/logs` | Paginated log (filter by `record_type`, `start_date`, `end_date`) |
| `GET` | `/api/v1/audit/tampering-alerts` | Entries where `is_tampered = true` |
| `POST` | `/api/v1/audit/verify/{record_id}` | Verify single block; flags if tampered |
| `GET` | `/api/v1/audit/chain-integrity` | Full chain walk — returns `is_valid`, `total_blocks`, `invalid_blocks` |
| `GET` | `/api/v1/audit/export` | Export as JSON or CSV (`?format=csv`) |

## Verification Workflow

### Routine integrity check (automated)

```
GET /api/v1/audit/chain-integrity
→ { "is_valid": true, "total_blocks": 200, "invalid_blocks": [] }
```

### Investigating a suspect record

```
POST /api/v1/audit/verify/42
→ { "is_valid": false, "record_id": 42, "message": "Record integrity check failed" }
```

The entry is automatically flagged as tampered. Follow up with:

```
GET /api/v1/audit/tampering-alerts
→ [ { "id": 42, "record_type": "medical_record", "is_tampered": true, ... } ]
```

## Transaction Safety

`create_audit_entry` calls `db.flush()`, not `db.commit()`. This means:

- If the outer transaction rolls back (e.g., a validation error after the audit call),
  the audit entry is also rolled back — no orphaned audit records for actions that never happened.
- The caller must call `db.commit()` to persist both the entity and the audit entry together.

## Testing

The test suite in `backend/tests/test_blockchain.py` covers:

- Hash determinism and uniqueness
- Genesis block (`previous_hash = "0"`)
- Chain linkage across multiple entries
- `verify_record_integrity` — valid, missing, and tampered cases
- `flag_tampered_record` — sets the flag
- `verify_chain_integrity` — empty chain, valid chain, broken link
- HTTP endpoints — 200/404, admin-only enforcement

Run:

```bash
cd project/backend
pytest tests/test_blockchain.py -v
```

## Integration with Behavioural Anomaly Detection

Audit chain write events serve as the trigger for a second, independent layer of security monitoring. After every call to `create_audit_entry`, the endpoint handlers in `medical_records.py` and `appointments.py` enqueue a background task that invokes `anomaly_service.analyze_and_alert()`. The anomaly service extracts eight behavioural features from the acting user's recent audit history, scores the session with a role-specific IsolationForest model, and — when the anomaly score exceeds 0.50 — persists an `AnomalyAlert` record in the `anomaly_alerts` table, linked back to the originating `audit_chain` row via `audit_entry_id`.

This means the blockchain audit chain remains the authoritative tamper-evident log for *what* happened, while the anomaly layer analyses *who* is doing it and whether the behaviour pattern is statistically unusual for that user's role. Both systems are independently queryable from the admin dashboard. The anomaly background task is fully wrapped in try/except and cannot affect the outcome of the primary request or the audit chain write.
