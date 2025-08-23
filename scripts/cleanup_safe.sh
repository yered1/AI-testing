#!/bin/bash
# Destination: patches/v2.0.0/scripts/cleanup_safe.sh
# Rationale: Remove OS-specific junk files and Python cache that shouldn't be in version control
# This script safely removes common development artifacts without touching important files

set -e

echo "🧹 Starting repository cleanup..."

# Counter for removed items
removed_count=0

# Remove macOS specific files
if find . -name "__MACOSX" -type d 2>/dev/null | grep -q .; then
    echo "Removing __MACOSX directories..."
    find . -name "__MACOSX" -type d -exec rm -rf {} + 2>/dev/null || true
    ((removed_count++))
fi

if find . -name ".DS_Store" -type f 2>/dev/null | grep -q .; then
    echo "Removing .DS_Store files..."
    find . -name ".DS_Store" -type f -delete 2>/dev/null || true
    ((removed_count++))
fi

# Remove Python cache
if find . -name "__pycache__" -type d 2>/dev/null | grep -q .; then
    echo "Removing __pycache__ directories..."
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    ((removed_count++))
fi

if find . -name "*.pyc" -type f 2>/dev/null | grep -q .; then
    echo "Removing .pyc files..."
    find . -name "*.pyc" -type f -delete 2>/dev/null || true
    ((removed_count++))
fi

if find . -name "*.pyo" -type f 2>/dev/null | grep -q .; then
    echo "Removing .pyo files..."
    find . -name "*.pyo" -type f -delete 2>/dev/null || true
    ((removed_count++))
fi

# Remove pytest cache
if find . -name ".pytest_cache" -type d 2>/dev/null | grep -q .; then
    echo "Removing .pytest_cache directories..."
    find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
    ((removed_count++))
fi

# Remove mypy cache
if find . -name ".mypy_cache" -type d 2>/dev/null | grep -q .; then
    echo "Removing .mypy_cache directories..."
    find . -name ".mypy_cache" -type d -exec rm -rf {} + 2>/dev/null || true
    ((removed_count++))
fi

# Remove coverage reports
if find . -name ".coverage" -type f 2>/dev/null | grep -q .; then
    echo "Removing .coverage files..."
    find . -name ".coverage" -type f -delete 2>/dev/null || true
    ((removed_count++))
fi

if find . -name "htmlcov" -type d 2>/dev/null | grep -q .; then
    echo "Removing htmlcov directories..."
    find . -name "htmlcov" -type d -exec rm -rf {} + 2>/dev/null || true
    ((removed_count++))
fi

if [ $removed_count -eq 0 ]; then
    echo "✅ Repository is already clean!"
else
    echo "✅ Cleanup complete! Removed $removed_count types of artifacts."
fi

echo ""
echo "💡 Tip: Run 'git status' to verify no important files were affected."