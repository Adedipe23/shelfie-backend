#!/usr/bin/env python3
"""
Comprehensive test runner for ISMS backend.
This script runs all tests with proper coverage reporting and categorization.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="ISMS Backend Test Runner")
    parser.add_argument(
        "--category",
        choices=["all", "unit", "integration", "api", "models", "services", "core"],
        default="all",
        help="Test category to run",
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        default=True,
        help="Run with coverage reporting",
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--fast", action="store_true", help="Skip slow tests")
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")

    args = parser.parse_args()

    # Set environment for testing
    os.environ["ENV_MODE"] = "testing"
    os.environ["SQLITE_DATABASE_URI"] = "sqlite+aiosqlite:///:memory:"

    # Base pytest command
    cmd = ["python", "-m", "pytest"]

    # Add coverage if requested
    if args.coverage:
        cmd.extend(
            [
                "--cov=app",
                "--cov-report=term-missing",
                "--cov-report=html:htmlcov",
                "--cov-report=xml",
                "--cov-fail-under=55",
            ]
        )

    # Add verbosity
    if args.verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")

    # Add parallel execution
    if args.parallel:
        cmd.extend(["-n", "auto"])

    # Skip slow tests if requested
    if args.fast:
        cmd.extend(["-m", "not slow"])

    # Add test paths and markers based on category
    if args.category == "all":
        cmd.append("tests/")
    elif args.category == "api":
        cmd.extend(["-m", "api", "tests/api/"])
    elif args.category == "models":
        cmd.extend(["-m", "models", "tests/models/"])
    elif args.category == "services":
        cmd.extend(["-m", "services", "tests/services/"])
    elif args.category == "core":
        cmd.extend(["-m", "core", "tests/core/"])
    elif args.category == "unit":
        # Unit tests include models, core, services, tasks, and utils
        cmd.extend(
            [
                "-m",
                "models or core or services or tasks or utils",
                "tests/models/",
                "tests/core/",
                "tests/services/",
                "tests/tasks/",
                "tests/utils/",
            ]
        )
    elif args.category == "integration":
        cmd.extend(["-m", "integration", "tests/api/"])

    # Run the tests
    success = run_command(cmd, f"Running {args.category} tests")

    if success and args.coverage:
        print(f"\n{'='*60}")
        print("📊 Coverage Report Generated")
        print("📁 HTML Report: htmlcov/index.html")
        print("📄 XML Report: coverage.xml")
        print(f"{'='*60}")

    # Print summary
    print(f"\n{'='*60}")
    if success:
        print("🎉 All tests passed successfully!")
        print("✅ Test suite execution completed")
    else:
        print("💥 Some tests failed!")
        print("❌ Check the output above for details")
    print(f"{'='*60}")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
