#!/bin/bash

# Setup script for pre-commit hooks
# This script installs pre-commit and sets up the hooks

echo "Setting up pre-commit hooks..."

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "Warning: Not in a virtual environment. Please activate your virtual environment first."
    echo "Example: source venv/bin/activate"
    exit 1
fi

# Install pre-commit
echo "Installing pre-commit..."
pip install pre-commit

# Install the pre-commit hooks
echo "Installing pre-commit hooks..."
pre-commit install

# Copy the tracked pre-commit hook to .git/hooks
echo "Copying pre-commit hook..."
cp hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

echo "✅ Pre-commit hooks installed successfully!"
echo ""
echo "The pre-commit hook will now run tests before each commit."
echo "If tests fail, the commit will be aborted."
echo ""
echo "To test the hook, try making a commit:"
echo "  git add ."
echo "  git commit -m 'test commit'" 