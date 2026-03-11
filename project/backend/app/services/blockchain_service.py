"""
Blockchain Integrity Service

This module provides hash generation and verification functions for the
blockchain-inspired audit chain that ensures medical record integrity.
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
    Generate SHA-256 hash for a medical record.
    
    This function creates a tamper-proof hash by combining:
    - record_data: The actual medical record content
    - timestamp: When the record was created/modified
    - user_id: Who performed the operation
    - previous_hash: Hash of the previous block in the chain
    
    Args:
        record_data: Dictionary containing the medical record data
        timestamp: Timestamp when the record was created/modified
        user_id: ID of the user who created/modified the record
        previous_hash: Hash of the previous audit chain entry (use "0" for genesis block)
    
    Returns:
        str: 64-character hexadecimal SHA-256 hash digest
    
    Example:
        >>> record = {"diagnosis": "Common cold", "prescription": "Rest"}
        >>> ts = datetime(2024, 1, 1, 12, 0, 0)
        >>> hash_val = generate_hash(record, ts, 123, "0")
        >>> len(hash_val)
        64
    """
    # Handle None values by converting to empty string/dict
    if record_data is None:
        record_data = {}
    if previous_hash is None:
        previous_hash = "0"
    
    # Create hash input structure
    hash_input = {
        'record_data': record_data,
        'timestamp': timestamp.isoformat() if timestamp else datetime.utcnow().isoformat(),
        'user_id': user_id,
        'previous_hash': previous_hash
    }
    
    # Convert to JSON string with sorted keys for consistency
    # This ensures the same input always produces the same hash
    hash_string = json.dumps(hash_input, sort_keys=True, ensure_ascii=True)
    
    # Generate SHA-256 hash
    hash_bytes = hashlib.sha256(hash_string.encode('utf-8')).hexdigest()
    
    return hash_bytes



def create_audit_entry(
    db: Session,
    medical_record: MedicalRecord,
    user_id: int
) -> AuditChain:
    """
    Create an audit chain entry for a medical record.
    
    This function:
    1. Gets the previous hash from the last audit entry (or "0" for genesis)
    2. Extracts record data from the medical record
    3. Generates a hash using the record data, timestamp, user_id, and previous_hash
    4. Creates a new AuditChain entry
    5. Links it to the medical record
    6. Saves to database
    
    Args:
        db: Database session
        medical_record: MedicalRecord object to create audit entry for
        user_id: ID of the user performing the operation
    
    Returns:
        AuditChain: The created audit chain entry
    
    Example:
        >>> from app.db.session import SessionLocal
        >>> db = SessionLocal()
        >>> record = db.query(MedicalRecord).first()
        >>> audit_entry = create_audit_entry(db, record, user_id=123)
        >>> audit_entry.hash
        'a1b2c3d4...'
    """
    # Get the previous hash from the last audit entry
    last_audit_entry = db.query(AuditChain).order_by(AuditChain.id.desc()).first()
    previous_hash = last_audit_entry.hash if last_audit_entry else "0"
    
    # Extract record data from medical record
    record_data = {
        "consultation_notes": medical_record.consultation_notes,
        "diagnosis": medical_record.diagnosis,
        "prescription": medical_record.prescription,
        "patient_id": medical_record.patient_id,
        "doctor_id": medical_record.doctor_id,
        "version_number": medical_record.version_number
    }
    
    # Generate timestamp
    timestamp = datetime.utcnow()
    
    # Generate hash for the new record
    hash_value = generate_hash(
        record_data=record_data,
        timestamp=timestamp,
        user_id=user_id,
        previous_hash=previous_hash
    )
    
    # Create new AuditChain entry
    audit_entry = AuditChain(
        record_id=medical_record.id,
        record_type="medical_record",
        record_data=record_data,
        hash=hash_value,
        previous_hash=previous_hash,
        timestamp=timestamp,
        user_id=user_id,
        is_tampered=False
    )
    
    # Add to session (don't commit - let caller handle transaction)
    db.add(audit_entry)
    db.flush()  # Flush to get the ID
    
    return audit_entry


def verify_record_integrity(
    db: Session,
    medical_record_id: int
) -> bool:
    """
    Verify the integrity of a medical record by recomputing its hash.

    This function:
    1. Fetches the audit_chain entry for the medical record
    2. Fetches the actual medical_record data
    3. Extracts record data (consultation_notes, diagnosis, prescription, patient_id, doctor_id, version_number)
    4. Recomputes hash using generate_hash() with the same inputs (record_data, timestamp, user_id, previous_hash)
    5. Compares recomputed hash with stored hash in audit_chain
    6. Returns verification result (True if match, False if mismatch)

    Args:
        db: Database session
        medical_record_id: ID of the medical record to verify

    Returns:
        bool: True if integrity is verified (hash matches), False if tampered (hash mismatch)

    Raises:
        ValueError: If audit entry or medical record is not found

    Example:
        >>> from app.db.session import SessionLocal
        >>> db = SessionLocal()
        >>> is_valid = verify_record_integrity(db, medical_record_id=123)
        >>> if not is_valid:
        ...     print("Tampering detected!")
    """
    # Fetch the audit entry for this medical record
    audit_entry = db.query(AuditChain).filter(
        AuditChain.record_id == medical_record_id,
        AuditChain.record_type == "medical_record"
    ).order_by(AuditChain.id.desc()).first()

    if not audit_entry:
        raise ValueError(f"No audit entry found for medical record ID {medical_record_id}")

    # Fetch the actual medical record
    medical_record = db.query(MedicalRecord).filter(
        MedicalRecord.id == medical_record_id
    ).first()

    if not medical_record:
        raise ValueError(f"Medical record with ID {medical_record_id} not found")

    # Extract record data from the medical record
    record_data = {
        "consultation_notes": medical_record.consultation_notes,
        "diagnosis": medical_record.diagnosis,
        "prescription": medical_record.prescription,
        "patient_id": medical_record.patient_id,
        "doctor_id": medical_record.doctor_id,
        "version_number": medical_record.version_number
    }

    # Recompute hash using the same inputs as when it was created
    recomputed_hash = generate_hash(
        record_data=record_data,
        timestamp=audit_entry.timestamp,
        user_id=audit_entry.user_id,
        previous_hash=audit_entry.previous_hash
    )

    # Compare recomputed hash with stored hash
    is_valid = (recomputed_hash == audit_entry.hash)

    return is_valid



def verify_record_integrity(
    db: Session,
    medical_record_id: int
) -> bool:
    """
    Verify the integrity of a medical record by recomputing its hash.
    
    This function:
    1. Fetches the audit_chain entry for the medical record
    2. Fetches the actual medical_record data
    3. Extracts record data (consultation_notes, diagnosis, prescription, patient_id, doctor_id, version_number)
    4. Recomputes hash using generate_hash() with the same inputs (record_data, timestamp, user_id, previous_hash)
    5. Compares recomputed hash with stored hash in audit_chain
    6. Returns verification result (True if match, False if mismatch)
    
    Args:
        db: Database session
        medical_record_id: ID of the medical record to verify
    
    Returns:
        bool: True if integrity is verified (hash matches), False if tampered (hash mismatch)
    
    Raises:
        ValueError: If audit entry or medical record is not found
    
    Example:
        >>> from app.db.session import SessionLocal
        >>> db = SessionLocal()
        >>> is_valid = verify_record_integrity(db, medical_record_id=123)
        >>> if not is_valid:
        ...     print("Tampering detected!")
    """
    # Fetch the audit entry for this medical record
    audit_entry = db.query(AuditChain).filter(
        AuditChain.record_id == medical_record_id,
        AuditChain.record_type == "medical_record"
    ).order_by(AuditChain.id.desc()).first()
    
    if not audit_entry:
        raise ValueError(f"No audit entry found for medical record ID {medical_record_id}")
    
    # Fetch the actual medical record
    medical_record = db.query(MedicalRecord).filter(
        MedicalRecord.id == medical_record_id
    ).first()
    
    if not medical_record:
        raise ValueError(f"Medical record with ID {medical_record_id} not found")
    
    # Extract record data from the medical record
    record_data = {
        "consultation_notes": medical_record.consultation_notes,
        "diagnosis": medical_record.diagnosis,
        "prescription": medical_record.prescription,
        "patient_id": medical_record.patient_id,
        "doctor_id": medical_record.doctor_id,
        "version_number": medical_record.version_number
    }
    
    # Recompute hash using the same inputs as when it was created
    recomputed_hash = generate_hash(
        record_data=record_data,
        timestamp=audit_entry.timestamp,
        user_id=audit_entry.user_id,
        previous_hash=audit_entry.previous_hash
    )
    
    # Compare recomputed hash with stored hash
    is_valid = (recomputed_hash == audit_entry.hash)
    
    return is_valid


def verify_chain_integrity(db: Session) -> Dict[str, Any]:
    """
    Verify the integrity of the entire audit chain.

    This function performs comprehensive chain verification by:
    1. Checking that the genesis block has previous_hash = "0"
    2. Verifying each block's hash is correctly computed
    3. Verifying previous_hash links form a valid chain
    4. Detecting any breaks or inconsistencies in the chain

    Args:
        db: Database session

    Returns:
        Dict containing:
            - is_valid (bool): True if entire chain is valid, False otherwise
            - total_blocks (int): Total number of blocks in the chain
            - verified_blocks (int): Number of blocks successfully verified
            - inconsistencies (list): List of detected inconsistencies with details

    Example:
        >>> from app.db.session import SessionLocal
        >>> db = SessionLocal()
        >>> result = verify_chain_integrity(db)
        >>> if not result['is_valid']:
        ...     print(f"Chain broken! {len(result['inconsistencies'])} issues found")
        ...     for issue in result['inconsistencies']:
        ...         print(f"Block {issue['block_id']}: {issue['error']}")
    """
    # Fetch all audit chain entries ordered by ID (chronological order)
    all_blocks = db.query(AuditChain).order_by(AuditChain.id.asc()).all()

    # Initialize result structure
    result = {
        'is_valid': True,
        'total_blocks': len(all_blocks),
        'verified_blocks': 0,
        'inconsistencies': []
    }

    # Empty chain is technically valid
    if len(all_blocks) == 0:
        return result

    # Verify genesis block
    genesis_block = all_blocks[0]
    if genesis_block.previous_hash != "0":
        result['is_valid'] = False
        result['inconsistencies'].append({
            'block_id': genesis_block.id,
            'block_index': 0,
            'error': 'Genesis block must have previous_hash = "0"',
            'expected': "0",
            'actual': genesis_block.previous_hash
        })

    # Verify genesis block's hash is correctly computed
    genesis_hash = generate_hash(
        record_data=genesis_block.record_data,
        timestamp=genesis_block.timestamp,
        user_id=genesis_block.user_id,
        previous_hash=genesis_block.previous_hash
    )

    if genesis_hash != genesis_block.hash:
        result['is_valid'] = False
        result['inconsistencies'].append({
            'block_id': genesis_block.id,
            'block_index': 0,
            'error': 'Genesis block hash mismatch - block may be corrupted',
            'expected': genesis_hash,
            'actual': genesis_block.hash
        })
    else:
        result['verified_blocks'] += 1

    # Verify subsequent blocks
    for i in range(1, len(all_blocks)):
        current_block = all_blocks[i]
        previous_block = all_blocks[i - 1]

        # Check 1: Verify previous_hash links to previous block
        if current_block.previous_hash != previous_block.hash:
            result['is_valid'] = False
            result['inconsistencies'].append({
                'block_id': current_block.id,
                'block_index': i,
                'error': 'Chain link broken - previous_hash does not match previous block hash',
                'expected': previous_block.hash,
                'actual': current_block.previous_hash,
                'previous_block_id': previous_block.id
            })

        # Check 2: Verify current block's hash is correctly computed
        recomputed_hash = generate_hash(
            record_data=current_block.record_data,
            timestamp=current_block.timestamp,
            user_id=current_block.user_id,
            previous_hash=current_block.previous_hash
        )

        if recomputed_hash != current_block.hash:
            result['is_valid'] = False
            result['inconsistencies'].append({
                'block_id': current_block.id,
                'block_index': i,
                'error': 'Block hash mismatch - block may be corrupted or tampered',
                'expected': recomputed_hash,
                'actual': current_block.hash
            })
        else:
            result['verified_blocks'] += 1

    return result



def verify_chain_integrity(db: Session) -> Dict[str, Any]:
    """
    Verify the integrity of the entire audit chain.
    
    This function performs comprehensive chain verification by:
    1. Checking that the genesis block has previous_hash = "0"
    2. Verifying each block's hash is correctly computed
    3. Verifying previous_hash links form a valid chain
    4. Detecting any breaks or inconsistencies in the chain
    
    Args:
        db: Database session
    
    Returns:
        Dict containing:
            - is_valid (bool): True if entire chain is valid, False otherwise
            - total_blocks (int): Total number of blocks in the chain
            - verified_blocks (int): Number of blocks successfully verified
            - inconsistencies (list): List of detected inconsistencies with details
    
    Example:
        >>> from app.db.session import SessionLocal
        >>> db = SessionLocal()
        >>> result = verify_chain_integrity(db)
        >>> if not result['is_valid']:
        ...     print(f"Chain broken! {len(result['inconsistencies'])} issues found")
        ...     for issue in result['inconsistencies']:
        ...         print(f"Block {issue['block_id']}: {issue['error']}")
    """
    # Fetch all audit chain entries ordered by ID (chronological order)
    all_blocks = db.query(AuditChain).order_by(AuditChain.id.asc()).all()
    
    # Initialize result structure
    result = {
        'is_valid': True,
        'total_blocks': len(all_blocks),
        'verified_blocks': 0,
        'inconsistencies': []
    }
    
    # Empty chain is technically valid
    if len(all_blocks) == 0:
        return result
    
    # Verify genesis block
    genesis_block = all_blocks[0]
    if genesis_block.previous_hash != "0":
        result['is_valid'] = False
        result['inconsistencies'].append({
            'block_id': genesis_block.id,
            'block_index': 0,
            'error': 'Genesis block must have previous_hash = "0"',
            'expected': "0",
            'actual': genesis_block.previous_hash
        })
    
    # Verify genesis block's hash is correctly computed
    genesis_hash = generate_hash(
        record_data=genesis_block.record_data,
        timestamp=genesis_block.timestamp,
        user_id=genesis_block.user_id,
        previous_hash=genesis_block.previous_hash
    )
    
    if genesis_hash != genesis_block.hash:
        result['is_valid'] = False
        result['inconsistencies'].append({
            'block_id': genesis_block.id,
            'block_index': 0,
            'error': 'Genesis block hash mismatch - block may be corrupted',
            'expected': genesis_hash,
            'actual': genesis_block.hash
        })
    else:
        result['verified_blocks'] += 1
    
    # Verify subsequent blocks
    for i in range(1, len(all_blocks)):
        current_block = all_blocks[i]
        previous_block = all_blocks[i - 1]
        
        # Check 1: Verify previous_hash links to previous block
        if current_block.previous_hash != previous_block.hash:
            result['is_valid'] = False
            result['inconsistencies'].append({
                'block_id': current_block.id,
                'block_index': i,
                'error': 'Chain link broken - previous_hash does not match previous block hash',
                'expected': previous_block.hash,
                'actual': current_block.previous_hash,
                'previous_block_id': previous_block.id
            })
        
        # Check 2: Verify current block's hash is correctly computed
        recomputed_hash = generate_hash(
            record_data=current_block.record_data,
            timestamp=current_block.timestamp,
            user_id=current_block.user_id,
            previous_hash=current_block.previous_hash
        )
        
        if recomputed_hash != current_block.hash:
            result['is_valid'] = False
            result['inconsistencies'].append({
                'block_id': current_block.id,
                'block_index': i,
                'error': 'Block hash mismatch - block may be corrupted or tampered',
                'expected': recomputed_hash,
                'actual': current_block.hash
            })
        else:
            result['verified_blocks'] += 1
    
    return result
