"""
Blockchain Integrity Service

Provides hash generation and verification for the blockchain-inspired audit
chain that ensures tamper-proof integrity of all healthcare actions: medical
record creation/updates, appointment lifecycle events, and admin actions.
"""

import hashlib
import json
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.audit_chain import AuditChain
from app.models.medical_record import MedicalRecord


def generate_hash(
    record_data: Dict[str, Any],
    timestamp: datetime,
    user_id: int,
    previous_hash: str
) -> str:
    """
    Generate SHA-256 hash for an audit block.

    Combines record_data, timestamp, user_id, and previous_hash into a
    deterministic JSON string and returns its SHA-256 hex digest. The same
    inputs always produce the same hash, enabling tamper detection.

    Args:
        record_data: Dictionary containing the record content to hash
        timestamp: UTC timestamp when the record was created/modified
        user_id: ID of the user who performed the operation
        previous_hash: Hash of the previous block ("0" for genesis block)

    Returns:
        64-character hexadecimal SHA-256 hash digest
    """
    if record_data is None:
        record_data = {}
    if previous_hash is None:
        previous_hash = "0"

    hash_input = {
        'record_data': record_data,
        'timestamp': timestamp.isoformat() if timestamp else datetime.utcnow().isoformat(),
        'user_id': user_id,
        'previous_hash': previous_hash
    }

    hash_string = json.dumps(hash_input, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(hash_string.encode('utf-8')).hexdigest()


def create_audit_entry(
    db: Session,
    record_id: int,
    record_type: str,
    record_data: Dict[str, Any],
    user_id: int
) -> AuditChain:
    """
    Create a new audit chain block for any healthcare action.

    Generalized entry point for the audit chain. Supports all record types:
    'medical_record', 'appointment_created', 'appointment_cancelled',
    'appointment_rescheduled', 'appointment_status_updated', 'walk_in_registered'.

    Steps:
        1. Fetch previous_hash from the last audit entry (or "0" for genesis)
        2. Generate SHA-256 hash of (record_data, timestamp, user_id, previous_hash)
        3. Insert a new AuditChain row and flush to get its ID
        4. Return the entry (caller owns the transaction commit)

    Args:
        db: Database session
        record_id: ID of the record being audited (appointment.id, medical_record.id, etc.)
        record_type: Category string identifying the action type
        record_data: Dictionary of relevant fields for this action
        user_id: ID of the user who performed the action

    Returns:
        AuditChain: The newly created (unflushed) audit chain entry
    """
    last_entry = db.query(AuditChain).order_by(AuditChain.id.desc()).first()
    previous_hash = last_entry.hash if last_entry else "0"

    timestamp = datetime.utcnow()
    hash_value = generate_hash(
        record_data=record_data,
        timestamp=timestamp,
        user_id=user_id,
        previous_hash=previous_hash
    )

    audit_entry = AuditChain(
        record_id=record_id,
        record_type=record_type,
        record_data=record_data,
        hash=hash_value,
        previous_hash=previous_hash,
        timestamp=timestamp,
        user_id=user_id,
        is_tampered=False
    )

    db.add(audit_entry)
    db.flush()
    return audit_entry


def create_medical_record_audit_entry(
    db: Session,
    medical_record: MedicalRecord,
    user_id: int
) -> AuditChain:
    """
    Backward-compatible wrapper for creating a medical record audit entry.

    Extracts the relevant fields from a MedicalRecord model instance and
    delegates to create_audit_entry with record_type='medical_record'.

    Args:
        db: Database session
        medical_record: MedicalRecord ORM object
        user_id: ID of the user who created/updated the record

    Returns:
        AuditChain: The newly created audit chain entry
    """
    record_data = {
        "consultation_notes": medical_record.consultation_notes,
        "diagnosis": medical_record.diagnosis,
        "prescription": medical_record.prescription,
        "patient_id": medical_record.patient_id,
        "doctor_id": medical_record.doctor_id,
        "version_number": medical_record.version_number
    }
    return create_audit_entry(db, medical_record.id, "medical_record", record_data, user_id)


def flag_tampered_record(db: Session, record_id: int, record_type: str = "medical_record") -> None:
    """
    Mark the most recent audit entry for a record as tampered.

    Sets is_tampered=True on the latest AuditChain entry matching the given
    record_id and record_type. Called automatically when verify_record_integrity
    detects a hash mismatch.

    Args:
        db: Database session
        record_id: ID of the tampered record
        record_type: Record type to search in audit chain (default: 'medical_record')
    """
    audit_entry = db.query(AuditChain).filter(
        AuditChain.record_id == record_id,
        AuditChain.record_type == record_type
    ).order_by(AuditChain.id.desc()).first()

    if audit_entry and not audit_entry.is_tampered:
        audit_entry.is_tampered = True
        db.commit()


def verify_record_integrity(
    db: Session,
    record_id: int
) -> bool:
    """
    Verify the integrity of a medical record by recomputing its hash.

    Fetches the latest audit_chain entry for the record and recomputes the
    hash from the data stored in that entry (record_data, timestamp, user_id,
    previous_hash). If the recomputed hash differs from the stored hash, the
    audit entry has been tampered with and the function returns False.

    Args:
        db: Database session
        record_id: ID of the medical record to verify

    Returns:
        bool: True if integrity verified (hash matches), False if tampered

    Raises:
        ValueError: If no audit entry is found for the given record ID
    """
    audit_entry = db.query(AuditChain).filter(
        AuditChain.record_id == record_id,
        AuditChain.record_type == "medical_record"
    ).order_by(AuditChain.id.desc()).first()

    if not audit_entry:
        raise ValueError(f"No audit entry found for medical record ID {record_id}")

    recomputed_hash = generate_hash(
        record_data=audit_entry.record_data,
        timestamp=audit_entry.timestamp,
        user_id=audit_entry.user_id,
        previous_hash=audit_entry.previous_hash
    )

    return recomputed_hash == audit_entry.hash


def verify_chain_integrity(db: Session) -> Dict[str, Any]:
    """
    Verify the integrity of the entire audit chain.

    Performs comprehensive chain verification:
        1. Genesis block must have previous_hash = "0"
        2. Each block's hash must match its recomputed value
        3. Each block's previous_hash must match the prior block's hash

    Args:
        db: Database session

    Returns:
        Dict with keys:
            - is_valid (bool): True if entire chain is valid
            - total_blocks (int): Total number of blocks
            - verified_blocks (int): Blocks that passed verification
            - inconsistencies (list): Detected issues with block details
    """
    all_blocks = db.query(AuditChain).order_by(AuditChain.id.asc()).all()

    result: Dict[str, Any] = {
        'is_valid': True,
        'total_blocks': len(all_blocks),
        'verified_blocks': 0,
        'inconsistencies': []
    }

    if not all_blocks:
        return result

    # Verify genesis block
    genesis = all_blocks[0]
    if genesis.previous_hash != "0":
        result['is_valid'] = False
        result['inconsistencies'].append({
            'block_id': genesis.id,
            'block_index': 0,
            'error': 'Genesis block must have previous_hash = "0"',
            'expected': "0",
            'actual': genesis.previous_hash
        })

    genesis_hash = generate_hash(
        record_data=genesis.record_data,
        timestamp=genesis.timestamp,
        user_id=genesis.user_id,
        previous_hash=genesis.previous_hash
    )
    if genesis_hash != genesis.hash:
        result['is_valid'] = False
        result['inconsistencies'].append({
            'block_id': genesis.id,
            'block_index': 0,
            'error': 'Genesis block hash mismatch — block may be corrupted',
            'expected': genesis_hash,
            'actual': genesis.hash
        })
    else:
        result['verified_blocks'] += 1

    # Verify subsequent blocks
    for i in range(1, len(all_blocks)):
        current = all_blocks[i]
        previous = all_blocks[i - 1]

        if current.previous_hash != previous.hash:
            result['is_valid'] = False
            result['inconsistencies'].append({
                'block_id': current.id,
                'block_index': i,
                'error': 'Chain link broken — previous_hash does not match previous block hash',
                'expected': previous.hash,
                'actual': current.previous_hash,
                'previous_block_id': previous.id
            })

        recomputed = generate_hash(
            record_data=current.record_data,
            timestamp=current.timestamp,
            user_id=current.user_id,
            previous_hash=current.previous_hash
        )
        if recomputed != current.hash:
            result['is_valid'] = False
            result['inconsistencies'].append({
                'block_id': current.id,
                'block_index': i,
                'error': 'Block hash mismatch — block may be corrupted or tampered',
                'expected': recomputed,
                'actual': current.hash
            })
        else:
            result['verified_blocks'] += 1

    return result
