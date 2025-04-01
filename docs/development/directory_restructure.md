# Directory Structure Restructuring Plan

## Current Structure Issue

The current nested directory structure (`monitorpy/monitorpy/`) is causing import problems:

```
monitorpy/
├── monitorpy/
│   ├── __init__.py
│   ├── api/
│   ├── cli.py
│   ├── core/
│   ├── plugins/
│   └── utils/
├── monitorpy.egg-info/
├── setup.py
└── tests/
```

This structure:
- Causes confusion with imports (`monitorpy.monitorpy.module` vs `monitorpy.module`)
- Requires special handling in scripts and test code
- Makes development environment setup more complicated
- Is not following standard Python package conventions

## Proposed Structure

We should restructure the project to follow standard Python package conventions:

```
monitorpy/
├── __init__.py
├── api/
├── cli.py
├── core/
├── plugins/
└── utils/
tests/
setup.py
```

This structure:
- Uses a single level for the main package
- Moves tests outside the package
- Follows standard Python package conventions
- Simplifies imports (`monitorpy.module`)

## Implementation Steps

1. **Create a temporary branch**:
   ```bash
   git checkout -b restructure-directories
   ```

2. **Move files to the new structure**:
   ```bash
   # Create new directory structure
   mkdir -p new_structure/monitorpy
   mkdir -p new_structure/tests
   
   # Copy files to new structure
   cp -r monitorpy/monitorpy/* new_structure/monitorpy/
   cp -r monitorpy/tests/* new_structure/tests/
   cp monitorpy/setup.py new_structure/
   cp monitorpy/requirements.txt new_structure/
   
   # Copy any other needed files
   cp README.md new_structure/
   cp LICENSE new_structure/
   ```

3. **Update imports in all Python files**:
   - Change all imports from `monitorpy.monitorpy.X` to `monitorpy.X`
   - Update relative imports accordingly

4. **Update setup.py**:
   - Ensure it points to the new package structure

5. **Update tests**:
   - Adjust import paths in test files

6. **Test the new structure**:
   ```bash
   cd new_structure
   pip install -e .
   pytest tests/
   ```

7. **Replace the old structure with the new one**:
   ```bash
   rm -rf monitorpy
   mv new_structure/* .
   rmdir new_structure
   ```

8. **Commit the changes**:
   ```bash
   git add .
   git commit -m "Restructure directory to eliminate nested package"
   ```

9. **Merge the branch**:
   ```bash
   git checkout main
   git merge restructure-directories
   ```

## Considerations

1. **Breaking Changes**:
   - This will break any external code that imports from `monitorpy.monitorpy`
   - Need to update documentation to reflect new import paths

2. **Version Bump**:
   - Consider a minor version bump (e.g., 0.2.0) to indicate changes

3. **Documentation**:
   - Update all examples and documentation to use the new import style

4. **Installation Verification**:
   - Test the package installation both in development and via pip
   - Ensure all command-line tools continue to work

## Migration Guide for Users

For users of the library, provide a migration guide:

```
# Migration Guide for MonitorPy 0.2.0

MonitorPy 0.2.0 restructures the package to follow standard conventions.
This requires updating your imports:

## Old imports:
from monitorpy.monitorpy.core import MonitorPlugin
from monitorpy.monitorpy.plugins import WebsiteStatusPlugin

## New imports:
from monitorpy.core import MonitorPlugin
from monitorpy.plugins import WebsiteStatusPlugin

All functionality remains the same, only the import paths have changed.
```