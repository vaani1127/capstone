"""
Database modules
Provides database connection, session management, and base models
"""
from app.db.session import (
    engine,
    SessionLocal,
    get_db,
    check_db_connection,
    close_db_connection
)
from app.db.base import Base, BaseModel
from app.db.exceptions import (
    DatabaseError,
    ConnectionError,
    TransactionError,
    RecordNotFoundError,
    DuplicateRecordError,
    handle_db_error
)

__all__ = [
    # Session management
    "engine",
    "SessionLocal",
    "get_db",
    "check_db_connection",
    "close_db_connection",
    # Base models
    "Base",
    "BaseModel",
    # Exceptions
    "DatabaseError",
    "ConnectionError",
    "TransactionError",
    "RecordNotFoundError",
    "DuplicateRecordError",
    "handle_db_error",
]
