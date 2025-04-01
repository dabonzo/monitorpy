# MonitorPy Agent Guidelines

## Build/Test Commands
- Install: `pip install -e .`
- Run all tests: `pytest tests/`
- Run specific test: `pytest tests/test_file.py::TestClass::test_method`
- Test with coverage: `pytest --cov=monitorpy tests/`
- Format code: `black monitorpy/` (always run this before committing)
- Lint: `flake8 monitorpy/`
- Sort imports: `isort monitorpy/`
- Type check: `mypy monitorpy/`
- Fix all lint errors before committing: `flake8 monitorpy/ --count`

## Code Style Guidelines
- Python 3.8+ compatible with type hints throughout
- Import order: stdlib → third-party → local, separated by newlines
- Use absolute imports from the package root (e.g., `from monitorpy.core import X`)
- Class names: `PascalCase`, functions/methods: `snake_case`, constants: `UPPER_SNAKE_CASE`
- Comprehensive docstrings with triple quotes, include Args/Returns sections
- Handle exceptions with appropriate logging and fallbacks
- Plugin architecture: inherit from `MonitorPlugin` abstract base class
- Error handling: catch specific exceptions and provide meaningful error messages
- Logging: use the module-level logger from utils.logging (`get_logger`)
- Line length: max 79 characters (use multi-line args for long code blocks)
- Use explicit noqa comments for deliberate lint violations (e.g., `# noqa: F401`)
- Test coverage: mock external dependencies, test success and failure cases
- Thread safety: Ensure plugins are thread-safe for parallel execution

## Project Summary
- MonitorPy is a plugin-based monitoring system with website, SSL, mail, and DNS monitoring capabilities
- Parallel execution system implemented using ThreadPoolExecutor to support checking many endpoints simultaneously
- Batch processing capabilities for handling large numbers of checks efficiently
- REST API and CLI interface with parallel execution support
- Key modules:
  - core/batch_runner.py: Implements parallel execution system
  - core/plugin_base.py: Base classes for plugins
  - plugins/: Individual monitoring plugin implementations
  - api/routes/batch.py: API endpoints for batch operations
- Documentation in docs/ includes dedicated parallel/ directory explaining features