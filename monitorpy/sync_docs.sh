#!/bin/bash
# sync_docs.sh - Keep documentation in sync across the repository

# Copy root README to package directory
cp -f README.md monitorpy/README.md

# Copy package specific documentation
cp -rf docs/* monitorpy/docs/

echo "Documentation synchronized"
