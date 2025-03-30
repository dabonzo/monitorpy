#!/bin/bash
# Setup script for initializing the MonitorPy Git repository

# Navigate to the project root
cd "$(dirname "$0")"

# Copy updated README to the monitorpy package directory
cp -f monitorpy/README.md monitorpy/monitorpy/

# Initialize Git repository if not already initialized
if [ ! -d .git ]; then
  git init
  echo "Git repository initialized"
else
  echo "Git repository already exists"
fi

# Add files to Git
git add .

# Make initial commit
git commit -m "Initial commit: MonitorPy monitoring system

This commit includes:
- Core plugin framework with proper Python package structure
- Website and SSL monitoring plugins
- Command-line interface
- Comprehensive documentation"

echo "Git repository initialized successfully!"
echo "You can now push this to a remote repository with:"
echo "  git remote add origin <your-repo-url>"
echo "  git push -u origin main"
