#!/usr/bin/env python3
"""
Database migration helper script for HealthSaathi
Provides convenient commands for managing Alembic migrations
"""

import sys
import os
import subprocess
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def run_command(command: list) -> int:
    """Run a shell command and return the exit code"""
    try:
        result = subprocess.run(command, check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Error: Command failed with exit code {e.returncode}")
        return e.returncode
    except FileNotFoundError:
        print("Error: Alembic not found. Please install dependencies: pip install -r requirements.txt")
        return 1


def print_usage():
    """Print usage information"""
    print("""
HealthSaathi Database Migration Helper

Usage: python migrate.py <command>

Commands:
  upgrade       Apply all pending migrations (upgrade to latest)
  downgrade     Rollback the last migration
  reset         Rollback all migrations and reapply them
  current       Show current migration version
  history       Show migration history
  seed          Apply seed data (for development/testing only)
  create <msg>  Create a new migration file
  help          Show this help message

Examples:
  python migrate.py upgrade          # Apply all migrations
  python migrate.py downgrade        # Rollback last migration
  python migrate.py reset            # Reset database
  python migrate.py current          # Check current version
  python migrate.py seed             # Load test data
  python migrate.py create "add user preferences"  # Create new migration

Environment:
  Set DATABASE_URL in .env file or as environment variable
  Format: postgresql://user:password@host:port/database
""")


def main():
    if len(sys.argv) < 2:
        print_usage()
        return 1

    command = sys.argv[1].lower()

    if command == "help" or command == "-h" or command == "--help":
        print_usage()
        return 0

    elif command == "upgrade":
        print("📦 Applying all pending migrations...")
        return run_command(["alembic", "upgrade", "head"])

    elif command == "downgrade":
        print("⏪ Rolling back last migration...")
        return run_command(["alembic", "downgrade", "-1"])

    elif command == "reset":
        print("🔄 Resetting database...")
        print("⏪ Rolling back all migrations...")
        result = run_command(["alembic", "downgrade", "base"])
        if result != 0:
            return result
        print("📦 Reapplying all migrations...")
        return run_command(["alembic", "upgrade", "head"])

    elif command == "current":
        print("📍 Current migration version:")
        return run_command(["alembic", "current"])

    elif command == "history":
        print("📜 Migration history:")
        return run_command(["alembic", "history"])

    elif command == "seed":
        print("🌱 Loading seed data...")
        print("Note: This will apply the seed data migration (002)")
        # First ensure we're at the base schema
        result = run_command(["alembic", "upgrade", "001"])
        if result != 0:
            return result
        # Then apply seed data
        return run_command(["alembic", "upgrade", "002"])

    elif command == "create":
        if len(sys.argv) < 3:
            print("Error: Please provide a migration message")
            print("Usage: python migrate.py create <message>")
            return 1
        message = " ".join(sys.argv[2:])
        print(f"📝 Creating new migration: {message}")
        return run_command(["alembic", "revision", "-m", message])

    else:
        print(f"Error: Unknown command '{command}'")
        print_usage()
        return 1


if __name__ == "__main__":
    sys.exit(main())
