# MonitorPy Development Guidelines

## Commands
- Install: `pip install -e .`
- Run: `python -m monitorpy.cli` or `monitorpy`
- Lint: `flake8 monitorpy`
- Format: `black monitorpy`
- Test: `pytest tests/`
- Single test: `pytest tests/test_file.py::test_function -v`
- Coverage: `pytest --cov=monitorpy tests/`

## Code Style
- Formatting: Black with default settings (120 character line length)
- Type hints: Always use for function parameters and return values
- Docstrings: Google style with Args/Returns sections
- Imports: Group standard lib, third-party, and local imports
- Naming: snake_case for variables/functions, CamelCase for classes
- Plugins: Inherit from MonitorPlugin, use @register_plugin decorator
- Error handling: Use specific exceptions, log appropriately
- Logging: Use monitorpy.utils.get_logger for module-specific logging
- Return values: Use CheckResult for plugin results, proper typing elsewhere