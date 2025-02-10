#!/bin/bash

# Copy the pre-commit hook to the .git/hooks/ directory
cp hooks/pre-commit .git/hooks/pre-commit

# Ensure the hook is executable
chmod +x .git/hooks/pre-commit

echo "Git hooks have been set up!"
