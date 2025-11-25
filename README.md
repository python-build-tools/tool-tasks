# tool-tasks

Zero-dependency Python task runner using pyproject.toml [tool.tasks]

## Features

- **Zero dependencies**: Uses only Python standard library (requires Python 3.11+ for `tomllib`)
- **Multiple task types**:
  - Shell commands
  - Task aliases
  - Task chains
  - Python module entry points
- **Simple configuration**: Define tasks in your `pyproject.toml` file
- **Automatic discovery**: Searches for `pyproject.toml` in current directory and parent directories

## Installation

```bash
pip install tool-tasks
```

## Usage

### Basic Usage

```bash
# List available tasks
task --list

# Run a task
task <task-name>

# Run a task with arguments
task <task-name> arg1 arg2
```

### Configuration

Define tasks in your `pyproject.toml` file under the `[tool.tasks]` section:

```toml
[tool.tasks]
# Simple shell command
hello = "echo 'Hello, World!'"

# Task alias (references another task)
greet = "hello"

# Task chain (runs multiple tasks in sequence)
ci = ["test", "lint", "build"]

# Shell command task
test = "pytest tests/"

# Dict-style task with cmd
[tool.tasks.build]
cmd = "python -m build"

# Dict-style task with chain
[tool.tasks.full-test]
chain = ["test", "lint"]

# Python entry point (calls a function from a module)
[tool.tasks.version]
call = "mypackage:print_version"
```

## Task Types

### 1. Shell Commands

Execute shell commands directly:

```toml
[tool.tasks]
test = "pytest tests/"
build = "python -m build"
```

### 2. Task Aliases

Reference other tasks by name:

```toml
[tool.tasks]
test = "pytest tests/"
t = "test"  # Alias for test task
```

### 3. Task Chains

Run multiple tasks in sequence. Stops on first failure:

```toml
[tool.tasks]
test = "pytest tests/"
lint = "ruff check ."
ci = ["test", "lint"]
```

### 4. Python Entry Points

Call Python functions directly:

```toml
[tool.tasks.version]
call = "mypackage:print_version"

# Can also call class methods
[tool.tasks.run-server]
call = "mypackage.server:Server.start"
```

The function/method should:
- Return an integer exit code (0 for success, non-zero for failure)
- Return `None` (treated as success)
- Access command-line arguments via `sys.argv`

## Examples

### Example pyproject.toml

```toml
[tool.tasks]
# Development tasks
dev = "python -m myapp --dev"
test = "pytest tests/ -v"
lint = "ruff check ."
format = "ruff format ."

# Build tasks
clean = "rm -rf dist/ build/ *.egg-info"
build = "python -m build"

# Task chains
check = ["lint", "test"]
ci = ["check", "build"]

# Python entry points
[tool.tasks.version]
call = "myapp:print_version"
```

### Running Tasks

```bash
# Run tests
task test

# Run CI pipeline (lint + test + build)
task ci

# Run development server
task dev

# Check version
task version
```

## Development

### Requirements

- Python 3.11 or higher (for `tomllib` from standard library)

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run tests with coverage
pytest tests/ --cov=src/tool_tasks --cov-report=term-missing
```

## License

See LICENSE file for details.
