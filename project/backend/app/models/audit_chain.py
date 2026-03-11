"""
Audit chain model for blockchain-inspired integrity verification
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import BaseModel


class AuditChain(BaseModel):
    """
    Audit chain model for blockchain-inspired audit trail and tamper detection.
    Each entry represents a block in the hash chain.
    
    Attributes:
        id: Primary key (inherited from Base)
        record_id: ID of the record being audited
        record_type: Type of record (e.g., 'medical_record', 'appointment')
        record_data: JSONB data of the record at time of audit
        hash: SHA-256 hash of record_data + timestamp + user_id + previous_hash
        previous_hash: Hash of the previous audit entry ("0" for genesis block)
        timestamp: When the audit entry was created
        user_id: Foreign key to users table (who performed the operation)
        is_tampered: Flag indicating if tampering was detected
    
    Relationships:
        user: User who performed the operation
    """
    __tablename__ = "audit_chain"
    
    record_id = Column(Integer, nullable=False, index=True)
    record_type = Column(String(50), nullable=False, index=True)
    record_data = Column(JSON, nullable=False)
    hash = Column(String(64), nullable=False, index=True)
    previous_hash = Column(String(64), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True)
    is_tampered = Column(Boolean, default=False, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_entries")
    
    def __repr__(self):
        return f"<AuditChain(id={self.id}, record_type='{self.record_type}', record_id={self.record_id}, is_tampered={self.is_tampered})>"
