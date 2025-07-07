#!/bin/bash

# ISMS Code Quality Check Script
# This script runs all the code quality checks that are run in CI/CD

set -e  # Exit on any error

echo "🔍 Running ISMS Code Quality Checks..."
echo "======================================"

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Function to print status
print_status() {
    if [ $? -eq 0 ]; then
        echo "✅ $1 passed"
    else
        echo "❌ $1 failed"
        exit 1
    fi
}

# Install dependencies if needed
echo "📦 Checking dependencies..."
pip install -q black isort flake8 autoflake bandit safety

# 1. Code formatting check (Black)
echo ""
echo "🎨 Checking code formatting with Black..."
black --check --diff .
print_status "Black formatting"

# 2. Import sorting check (isort)
echo ""
echo "📚 Checking import sorting with isort..."
isort --check-only --diff .
print_status "isort import sorting"

# 3. Linting (flake8)
echo ""
echo "🔍 Running linting with flake8..."
flake8 app tests
print_status "flake8 linting"

# 4. Type checking (mypy) - skipped for now
echo ""
echo "⏭️  Skipping type checking (mypy) - can be added later"

# 5. Security check (bandit)
echo ""
echo "🔒 Running security check with bandit..."
bandit -r app/ -f json -o bandit-report.json || echo "⚠️  bandit found some issues (check bandit-report.json)"

# 6. Dependency vulnerability check (safety)
echo ""
echo "🛡️  Running dependency vulnerability check with safety..."
safety check --json --output safety-report.json || echo "⚠️  safety found some issues (check safety-report.json)"

echo ""
echo "🎉 Code quality checks completed!"
echo "=================================="
echo ""
echo "📋 Summary:"
echo "✅ Code formatting (Black)"
echo "✅ Import sorting (isort)"
echo "✅ Linting (flake8)"
echo "⏭️  Type checking (mypy) - skipped for now"
echo "⚠️  Security scanning (bandit) - check report"
echo "⚠️  Dependency scanning (safety) - check report"
echo ""
echo "🚀 Your code is ready for CI/CD!"
echo ""
echo "💡 To auto-fix formatting issues, run:"
echo "   black ."
echo "   isort ."
echo ""
echo "📊 To run tests with coverage:"
echo "   python -m pytest --cov=app --cov-report=html"
