#!/usr/bin/env python
"""
Run script for the Integrated Supermarket Management System (ISMS).
This script provides commands for running the application, tests, and other common tasks.
"""

import os
import subprocess
import sys
from typing import List, Optional

import typer

app = typer.Typer(help="ISMS run script")


@app.command()
def dev(
    host: str = "127.0.0.1",
    port: int = 8000,
    reload: bool = True,
):
    """Run the application in development mode."""
    typer.echo(f"Starting development server at {host}:{port}")
    cmd = [
        "uvicorn",
        "app.main:app",
        "--host",
        host,
        "--port",
        str(port),
    ]
    if reload:
        cmd.append("--reload")

    subprocess.run(cmd)


@app.command()
def test(
    path: Optional[List[str]] = typer.Argument(None),
    coverage: bool = typer.Option(False, "--cov", help="Run with coverage report"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Verbose output"),
):
    """Run tests."""
    cmd = ["pytest"]

    if verbose:
        cmd.append("-v")

    if coverage:
        cmd.append("--cov=app")
        cmd.append("--cov-report=term")

    if path:
        cmd.extend(path)

    typer.echo(f"Running tests: {' '.join(cmd)}")
    subprocess.run(cmd)


@app.command()
def docker_test():
    """Run tests in Docker."""
    typer.echo("Running tests in Docker")
    cmd = [
        "docker-compose",
        "-f",
        "docker-compose.test.yml",
        "up",
        "--build",
        "--abort-on-container-exit",
    ]
    subprocess.run(cmd)


@app.command()
def docker_dev():
    """Run the application in Docker development mode."""
    typer.echo("Starting Docker development environment")
    cmd = [
        "docker-compose",
        "up",
        "--build",
    ]
    subprocess.run(cmd)


@app.command()
def init_db():
    """Initialize the database."""
    typer.echo("Initializing database")
    subprocess.run(["python", "manage.py", "init_db"])


@app.command()
def create_superuser():
    """Create a superuser."""
    typer.echo("Creating superuser")
    subprocess.run(["python", "manage.py", "create_superuser"])


if __name__ == "__main__":
    app()
