"""
Tests for database connection layer
"""
import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db import (
    SessionLocal,
    get_db,
    check_db_connection,
    engine,
    DatabaseError,
    ConnectionError as DBConnectionError,
    handle_db_error
)


class TestDatabaseConnection:
    """Test database connection and session management"""
    
    def test_engine_creation(self):
        """Test that database engine is created successfully"""
        assert engine is not None
        assert engine.url.database is not None
    
    def test_session_creation(self):
        """Test that database session can be created"""
        session = SessionLocal()
        assert session is not None
        session.close()
    
    def test_check_db_connection(self):
        """Test database connection health check"""
        result = check_db_connection()
        assert result is True, "Database connection should be healthy"
    
    def test_get_db_dependency(self):
        """Test get_db dependency function"""
        db_gen = get_db()
        db = next(db_gen)
        
        assert db is not None
        
        # Test that we can execute a simple query
        result = db.execute(text("SELECT 1"))
        assert result is not None
        
        # Close the generator
        try:
            next(db_gen)
        except StopIteration:
            pass
    
    def test_session_rollback_on_error(self):
        """Test that session rolls back on error"""
        db = SessionLocal()
        
        try:
            # Execute invalid SQL to trigger error
            db.execute(text("SELECT * FROM nonexistent_table"))
            db.commit()
        except SQLAlchemyError:
            db.rollback()
            # Should not raise exception after rollback
            result = db.execute(text("SELECT 1"))
            assert result is not None
        finally:
            db.close()
    
    def test_connection_pool_settings(self):
        """Test that connection pool is configured correctly"""
        pool = engine.pool
        assert pool.size() >= 0  # Pool should be initialized
        assert hasattr(pool, 'timeout')


class TestDatabaseExceptions:
    """Test custom database exceptions"""
    
    def test_database_error_creation(self):
        """Test DatabaseError can be created"""
        error = DatabaseError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
    
    def test_connection_error_creation(self):
        """Test ConnectionError can be created"""
        error = DBConnectionError("Connection failed")
        assert str(error) == "Connection failed"
        assert isinstance(error, DatabaseError)
    
    def test_handle_db_error(self):
        """Test error handling function"""
        # Create a mock SQLAlchemy error
        sql_error = SQLAlchemyError("Test error")
        
        result = handle_db_error(sql_error)
        assert isinstance(result, DatabaseError)
        assert result.original_error == sql_error


class TestSessionLifecycle:
    """Test database session lifecycle"""
    
    def test_session_commit(self):
        """Test session commit works"""
        db = SessionLocal()
        try:
            # Simple query that should succeed
            db.execute(text("SELECT 1"))
            db.commit()
        finally:
            db.close()
    
    def test_session_close(self):
        """Test session closes properly"""
        db = SessionLocal()
        db.close()
        
        # After closing, session should not be usable
        with pytest.raises(Exception):
            db.execute(text("SELECT 1"))
