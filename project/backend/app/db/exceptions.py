"""
Custom database exceptions for better error handling
"""
from sqlalchemy.exc import SQLAlchemyError


class DatabaseError(Exception):
    """Base exception for database errors"""
    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class ConnectionError(DatabaseError):
    """Exception raised when database connection fails"""
    pass


class TransactionError(DatabaseError):
    """Exception raised when database transaction fails"""
    pass


class RecordNotFoundError(DatabaseError):
    """Exception raised when a database record is not found"""
    pass


class DuplicateRecordError(DatabaseError):
    """Exception raised when attempting to create a duplicate record"""
    pass


def handle_db_error(error: SQLAlchemyError) -> DatabaseError:
    """
    Convert SQLAlchemy errors to custom database exceptions.
    
    Args:
        error: SQLAlchemy exception
        
    Returns:
        DatabaseError: Custom database exception
    """
    error_msg = str(error)
    
    if "connection" in error_msg.lower():
        return ConnectionError(
            "Failed to connect to database",
            original_error=error
        )
    elif "unique constraint" in error_msg.lower() or "duplicate" in error_msg.lower():
        return DuplicateRecordError(
            "Record with this identifier already exists",
            original_error=error
        )
    elif "not found" in error_msg.lower():
        return RecordNotFoundError(
            "Requested record not found",
            original_error=error
        )
    else:
        return TransactionError(
            f"Database transaction failed: {error_msg}",
            original_error=error
        )
