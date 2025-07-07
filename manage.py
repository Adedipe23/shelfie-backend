#!/usr/bin/env python
import asyncio
import logging
import os
import sys
from typing import Optional

import typer
import uvicorn
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory, create_db_and_tables
from app.core.logging import setup_logging
from app.core.password import get_password_hash
from app.models.user import User, UserRole

# Set up logging
setup_logging()
logger = logging.getLogger("app.cli")

# Create Typer app
app = typer.Typer(help="ISMS management CLI")


@app.command()
def runserver(
    host: str = "127.0.0.1",
    port: int = 8000,
    reload: bool = True,
):
    """Run the development server."""
    logger.info(f"Starting development server at {host}:{port}")

    # Configure reload excludes to prevent watching log files and database files
    reload_excludes = (
        [
            "*.log",
            "*.db",
            "*.sqlite*",
            "logs/*",
            "__pycache__/*",
            ".git/*",
            "venv/*",
            ".pytest_cache/*",
            "*.pyc",
            "debug_settings.py",  # Exclude our debug script
        ]
        if reload
        else None
    )

    # Also specify reload dirs to only watch specific directories
    reload_dirs = ["app/"] if reload else None

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        reload_excludes=reload_excludes,
        reload_dirs=reload_dirs,
    )


@app.command()
def runprod(
    host: str = "0.0.0.0",
    port: int = 8000,
    workers: Optional[int] = None,
):
    """Run the production server with gunicorn."""
    from app.core.settings import get_settings

    settings = get_settings()

    # Use workers from environment variable if not specified
    if workers is None:
        workers = settings.WORKERS

    logger.info(f"Starting production server at {host}:{port} with {workers} workers")

    # Use gunicorn for production with uvicorn workers
    import subprocess

    cmd = [
        "gunicorn",
        "app.main:app",
        "--worker-class",
        "uvicorn.workers.UvicornWorker",
        "--workers",
        str(workers),
        "--bind",
        f"{host}:{port}",
        "--access-logfile",
        "-",
        "--error-logfile",
        "-",
        "--log-level",
        settings.LOG_LEVEL.lower(),
        "--preload",  # Preload app for better memory usage
        "--max-requests",
        "1000",  # Restart workers after 1000 requests
        "--max-requests-jitter",
        "100",  # Add jitter to prevent thundering herd
        "--timeout",
        "30",  # Worker timeout
        "--keep-alive",
        "2",  # Keep-alive timeout
    ]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Production server failed to start: {e}")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        logger.info("Production server stopped by user")
        raise typer.Exit(0)


@app.command()
def create_user(
    email: str = typer.Option(..., prompt=True),
    password: str = typer.Option(..., prompt=True, hide_input=True),
    full_name: str = typer.Option(..., prompt=True),
    role: UserRole = typer.Option(UserRole.CASHIER, case_sensitive=False),
    superuser: bool = typer.Option(False),
):
    """Create a new user."""

    async def _create_user():
        async with async_session_factory() as session:
            # Check if user exists
            user = await User.get_by_email(session, email=email)
            if user:
                logger.error(f"User with email {email} already exists")
                return

            # Create user
            user_data = {
                "email": email,
                "password": password,
                "full_name": full_name,
                "role": role,
                "is_superuser": superuser,
            }
            user = await User.create(session, obj_in=user_data)
            logger.info(f"User created: {user.email} (ID: {user.id})")

    asyncio.run(_create_user())


@app.command()
def init_db():
    """Initialize the database."""

    async def _init_db():
        await create_db_and_tables()
        logger.info("Database initialized")

    asyncio.run(_init_db())


@app.command()
def create_superuser():
    """Create a superuser (admin) account."""
    create_user(
        email=typer.prompt("Email"),
        password=typer.prompt("Password", hide_input=True),
        full_name=typer.prompt("Full Name"),
        role=UserRole.ADMIN,
        superuser=True,
    )


@app.command()
def check_db():
    """Check database connection and status."""

    async def _check_db():
        try:
            from app.core.settings import get_settings

            settings = get_settings()

            logger.info(f"Environment: {settings.ENV_MODE}")
            logger.info(
                f"Database URI: {settings.DATABASE_URI or settings.SQLITE_DATABASE_URI}"
            )

            async with async_session_factory() as session:
                # Test basic connection
                result = await session.execute("SELECT 1")
                logger.info("✅ Database connection successful")

                # Check if tables exist
                from sqlmodel import SQLModel

                async with session.get_bind().begin() as conn:
                    # Get table names
                    if "postgresql" in str(session.get_bind().url):
                        result = await conn.execute(
                            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
                        )
                    else:
                        result = await conn.execute(
                            "SELECT name FROM sqlite_master WHERE type='table'"
                        )

                    tables = [row[0] for row in result.fetchall()]
                    if tables:
                        logger.info(
                            f"✅ Found {len(tables)} tables: {', '.join(tables)}"
                        )
                    else:
                        logger.warning(
                            "⚠️  No tables found. Run 'init_db' to create tables."
                        )

        except Exception as e:
            logger.error(f"❌ Database check failed: {e}")
            raise typer.Exit(1)

    asyncio.run(_check_db())


@app.command()
def reset_db():
    """Reset the database (DROP ALL TABLES and recreate)."""
    if not typer.confirm("⚠️  This will DELETE ALL DATA. Are you sure?"):
        logger.info("Database reset cancelled.")
        return

    async def _reset_db():
        try:
            from sqlmodel import SQLModel

            async with async_session_factory() as session:
                async with session.get_bind().begin() as conn:
                    # Drop all tables
                    await conn.run_sync(SQLModel.metadata.drop_all)
                    logger.info("🗑️  All tables dropped")

                    # Recreate tables
                    await conn.run_sync(SQLModel.metadata.create_all)
                    logger.info("✅ Tables recreated")

        except Exception as e:
            logger.error(f"❌ Database reset failed: {e}")
            raise typer.Exit(1)

    asyncio.run(_reset_db())


@app.command()
def backup_db(output_file: str = typer.Option(None, help="Output file path")):
    """Backup database (PostgreSQL only)."""

    async def _backup_db():
        try:
            from app.core.settings import get_settings

            settings = get_settings()

            if not settings.DATABASE_URI or "postgresql" not in settings.DATABASE_URI:
                logger.error("❌ Backup is only supported for PostgreSQL databases")
                raise typer.Exit(1)

            import subprocess
            from datetime import datetime

            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = f"isms_backup_{timestamp}.sql"
            else:
                backup_file = output_file

            # Extract connection details
            db_url = settings.DATABASE_URI
            # Parse postgresql+asyncpg://user:pass@host/db
            import re

            match = re.match(
                r"postgresql\+asyncpg://([^:]+):([^@]+)@([^/]+)/(.+)", db_url
            )
            if not match:
                logger.error("❌ Could not parse database URL")
                raise typer.Exit(1)

            user, password, host, database = match.groups()

            # Set environment variable for password
            env = os.environ.copy()
            env["PGPASSWORD"] = password

            # Run pg_dump
            cmd = [
                "pg_dump",
                "-h",
                host,
                "-U",
                user,
                "-d",
                database,
                "-f",
                backup_file,
                "--verbose",
            ]

            logger.info(f"Creating backup: {backup_file}")
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info(f"✅ Backup created successfully: {backup_file}")
            else:
                logger.error(f"❌ Backup failed: {result.stderr}")
                raise typer.Exit(1)

        except Exception as e:
            logger.error(f"❌ Backup failed: {e}")
            raise typer.Exit(1)

    asyncio.run(_backup_db())


@app.command()
def health_check():
    """Perform a comprehensive health check."""

    async def _health_check():
        try:
            logger.info("🔍 Performing health check...")

            # Check database
            async with async_session_factory() as session:
                await session.execute("SELECT 1")
                logger.info("✅ Database: OK")

            # Check if we can create tables
            await create_db_and_tables()
            logger.info("✅ Table creation: OK")

            # Check user model
            async with async_session_factory() as session:
                user_count = await session.execute("SELECT COUNT(*) FROM users")
                count = user_count.scalar()
                logger.info(f"✅ Users table: {count} users")

            logger.info("🎉 Health check completed successfully!")

        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            raise typer.Exit(1)

    asyncio.run(_health_check())


if __name__ == "__main__":
    app()
