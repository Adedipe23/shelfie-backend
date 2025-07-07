#!/bin/bash

# ISMS Code Quality Auto-Fix Script
# This script automatically fixes code formatting and import issues

set -e  # Exit on any error

echo "🔧 Auto-fixing ISMS Code Quality Issues..."
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Install dependencies if needed
echo "📦 Installing/checking dependencies..."
pip install -q black isort autoflake

# 1. Remove unused imports and variables
echo ""
echo "🧹 Removing unused imports and variables with autoflake..."
autoflake --remove-all-unused-imports --remove-unused-variables --in-place --recursive app tests
echo "✅ Unused imports and variables removed"

# 2. Sort imports
echo ""
echo "📚 Sorting imports with isort..."
isort .
echo "✅ Imports sorted"

# 3. Format code
echo ""
echo "🎨 Formatting code with Black..."
black .
echo "✅ Code formatted"

echo ""
echo "🎉 Code quality auto-fix completed!"
echo "==================================="
echo ""
echo "📋 What was fixed:"
echo "✅ Removed unused imports and variables"
echo "✅ Sorted imports according to PEP 8"
echo "✅ Formatted code according to Black style"
echo ""
echo "🔍 Next steps:"
echo "1. Review the changes with: git diff"
echo "2. Run quality checks: ./scripts/check_code_quality.sh"
echo "3. Run tests: python -m pytest"
echo "4. Commit your changes: git add . && git commit -m 'Fix code quality issues'"
echo ""
echo "🚀 Your code is now ready for CI/CD!"
