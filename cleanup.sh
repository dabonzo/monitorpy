#!/bin/bash
# cleanup.sh - Clean up project structure

# Remove duplicate setup files in the inner directory
rm -f monitorpy/monitorpy/setup.py monitorpy/monitorpy/requirements.txt

# Make sure the main documentation is properly synced
./sync_docs.sh

echo "Project structure cleaned up"
