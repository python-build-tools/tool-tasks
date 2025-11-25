"""Tests for the executor module."""

import sys
import tempfile
from pathlib import Path

import pytest

from tool_tasks.config import TaskConfig
from tool_tasks.executor import TaskExecutor


def test_execute_shell_command():
    """Test executing a simple shell command."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        pyproject = tmpdir_path / "pyproject.toml"
        pyproject.write_text("""
[tool.tasks]
hello = "echo hello"
""")

        config = TaskConfig(pyproject)
        executor = TaskExecutor(config)
        exit_code = executor.execute("hello")
        assert exit_code == 0


def test_execute_shell_command_with_args():
    """Test executing a shell command with additional arguments."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        pyproject = tmpdir_path / "pyproject.toml"
        pyproject.write_text("""
[tool.tasks]
echo = "echo"
""")

        config = TaskConfig(pyproject)
        executor = TaskExecutor(config)
        exit_code = executor.execute("echo", ["hello", "world"])
        assert exit_code == 0


def test_execute_failing_command():
    """Test executing a command that fails."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        pyproject = tmpdir_path / "pyproject.toml"
        pyproject.write_text("""
[tool.tasks]
fail = "exit 1"
""")

        config = TaskConfig(pyproject)
        executor = TaskExecutor(config)
        exit_code = executor.execute("fail")
        assert exit_code == 1


def test_execute_task_alias():
    """Test executing a task alias."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        pyproject = tmpdir_path / "pyproject.toml"
        pyproject.write_text("""
[tool.tasks]
original = "echo original"
alias = "original"
""")

        config = TaskConfig(pyproject)
        executor = TaskExecutor(config)
        exit_code = executor.execute("alias")
        assert exit_code == 0


def test_execute_task_chain():
    """Test executing a chain of tasks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        pyproject = tmpdir_path / "pyproject.toml"
        pyproject.write_text("""
[tool.tasks]
task1 = "echo task1"
task2 = "echo task2"
chain = ["task1", "task2"]
""")

        config = TaskConfig(pyproject)
        executor = TaskExecutor(config)
        exit_code = executor.execute("chain")
        assert exit_code == 0


def test_execute_task_chain_stops_on_failure():
    """Test that task chain stops on first failure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        pyproject = tmpdir_path / "pyproject.toml"
        pyproject.write_text("""
[tool.tasks]
task1 = "echo task1"
fail = "exit 1"
task2 = "echo task2"
chain = ["task1", "fail", "task2"]
""")

        config = TaskConfig(pyproject)
        executor = TaskExecutor(config)
        exit_code = executor.execute("chain")
        assert exit_code == 1


def test_execute_dict_cmd():
    """Test executing a dict task with cmd key."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        pyproject = tmpdir_path / "pyproject.toml"
        pyproject.write_text("""
[tool.tasks.hello]
cmd = "echo hello"
""")

        config = TaskConfig(pyproject)
        executor = TaskExecutor(config)
        exit_code = executor.execute("hello")
        assert exit_code == 0


def test_execute_dict_chain():
    """Test executing a dict task with chain key."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        pyproject = tmpdir_path / "pyproject.toml"
        pyproject.write_text("""
[tool.tasks]
task1 = "echo task1"
task2 = "echo task2"

[tool.tasks.mychain]
chain = ["task1", "task2"]
""")

        config = TaskConfig(pyproject)
        executor = TaskExecutor(config)
        exit_code = executor.execute("mychain")
        assert exit_code == 0


def test_execute_python_call():
    """Test executing a Python module entry point."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        pyproject = tmpdir_path / "pyproject.toml"
        pyproject.write_text("""
[tool.tasks.pycall]
call = "sys:exit"
""")

        # Create a simple Python module for testing
        module_dir = tmpdir_path / "testmodule"
        module_dir.mkdir()
        (module_dir / "__init__.py").write_text("""
def test_func():
    return 0

class TestClass:
    @staticmethod
    def test_method():
        return 0
""")

        # Add module to sys.path
        import sys
        sys.path.insert(0, str(tmpdir_path))

        try:
            config = TaskConfig(pyproject)
            executor = TaskExecutor(config)

            # Update task to call our test module
            config.tasks["pycall"]["call"] = "testmodule:test_func"
            exit_code = executor.execute("pycall")
            assert exit_code == 0

            # Test class method
            config.tasks["pycall"]["call"] = "testmodule:TestClass.test_method"
            exit_code = executor.execute("pycall")
            assert exit_code == 0
        finally:
            sys.path.pop(0)


def test_execute_python_call_with_args():
    """Test executing a Python call with arguments."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        pyproject = tmpdir_path / "pyproject.toml"
        pyproject.write_text("""
[tool.tasks.pycall]
call = "testmodule2:check_args"
""")

        # Create a module that checks sys.argv
        module_dir = tmpdir_path / "testmodule2"
        module_dir.mkdir()
        (module_dir / "__init__.py").write_text("""
import sys

def check_args():
    # sys.argv should contain the function path and any additional args
    if len(sys.argv) > 1 and sys.argv[1] == "test_arg":
        return 0
    return 1
""")

        import sys
        sys.path.insert(0, str(tmpdir_path))

        try:
            config = TaskConfig(pyproject)
            executor = TaskExecutor(config)
            exit_code = executor.execute("pycall", ["test_arg"])
            assert exit_code == 0
        finally:
            sys.path.pop(0)
            # Clean up imported module
            if "testmodule2" in sys.modules:
                del sys.modules["testmodule2"]


def test_execute_python_call_returns_none():
    """Test Python call that returns None."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        pyproject = tmpdir_path / "pyproject.toml"
        pyproject.write_text("""
[tool.tasks.pycall]
call = "testmodule3:returns_none"
""")

        module_dir = tmpdir_path / "testmodule3"
        module_dir.mkdir()
        (module_dir / "__init__.py").write_text("""
def returns_none():
    pass
""")

        import sys
        sys.path.insert(0, str(tmpdir_path))

        try:
            config = TaskConfig(pyproject)
            executor = TaskExecutor(config)
            exit_code = executor.execute("pycall")
            assert exit_code == 0
        finally:
            sys.path.pop(0)
            if "testmodule3" in sys.modules:
                del sys.modules["testmodule3"]


def test_execute_python_call_returns_non_int():
    """Test Python call that returns non-integer value."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        pyproject = tmpdir_path / "pyproject.toml"
        pyproject.write_text("""
[tool.tasks.pycall]
call = "testmodule4:returns_string"
""")

        module_dir = tmpdir_path / "testmodule4"
        module_dir.mkdir()
        (module_dir / "__init__.py").write_text("""
def returns_string():
    return "hello"
""")

        import sys
        sys.path.insert(0, str(tmpdir_path))

        try:
            config = TaskConfig(pyproject)
            executor = TaskExecutor(config)
            exit_code = executor.execute("pycall")
            assert exit_code == 0
        finally:
            sys.path.pop(0)
            if "testmodule4" in sys.modules:
                del sys.modules["testmodule4"]


def test_execute_python_call_invalid_format(capsys):
    """Test Python call with invalid format."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        pyproject = tmpdir_path / "pyproject.toml"
        pyproject.write_text("""
[tool.tasks.pycall]
call = "invalid_format"
""")

        config = TaskConfig(pyproject)
        executor = TaskExecutor(config)
        exit_code = executor.execute("pycall")
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Invalid call format" in captured.err


def test_execute_python_call_module_not_found(capsys):
    """Test Python call with non-existent module."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        pyproject = tmpdir_path / "pyproject.toml"
        pyproject.write_text("""
[tool.tasks.pycall]
call = "nonexistent_module:function"
""")

        config = TaskConfig(pyproject)
        executor = TaskExecutor(config)
        exit_code = executor.execute("pycall")
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Failed to import module" in captured.err


def test_execute_python_call_attribute_not_found(capsys):
    """Test Python call with non-existent attribute."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        pyproject = tmpdir_path / "pyproject.toml"
        pyproject.write_text("""
[tool.tasks.pycall]
call = "sys:nonexistent_function"
""")

        config = TaskConfig(pyproject)
        executor = TaskExecutor(config)
        exit_code = executor.execute("pycall")
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "not found" in captured.err


def test_circular_dependency_detection(capsys):
    """Test detection of circular task dependencies."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        pyproject = tmpdir_path / "pyproject.toml"
        pyproject.write_text("""
[tool.tasks]
task1 = "task2"
task2 = "task1"
""")

        config = TaskConfig(pyproject)
        executor = TaskExecutor(config)
        exit_code = executor.execute("task1")
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Circular dependency detected" in captured.err


def test_execute_invalid_dict_task(capsys):
    """Test executing an invalid dict task."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        pyproject = tmpdir_path / "pyproject.toml"
        pyproject.write_text("""
[tool.tasks.invalid]
unknown_key = "value"
""")

        config = TaskConfig(pyproject)
        executor = TaskExecutor(config)
        exit_code = executor.execute("invalid")
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Invalid task configuration" in captured.err


def test_execute_invalid_task_type(capsys):
    """Test executing a task with invalid type."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        pyproject = tmpdir_path / "pyproject.toml"
        pyproject.write_text("""
[tool.tasks]
invalid = 123
""")

        config = TaskConfig(pyproject)
        executor = TaskExecutor(config)
        exit_code = executor.execute("invalid")
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Invalid task configuration type" in captured.err


def test_execute_python_call_raises_exception(capsys):
    """Test Python call that raises an exception."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        pyproject = tmpdir_path / "pyproject.toml"
        pyproject.write_text("""
[tool.tasks.pycall]
call = "testmodule5:raises_error"
""")

        module_dir = tmpdir_path / "testmodule5"
        module_dir.mkdir()
        (module_dir / "__init__.py").write_text("""
def raises_error():
    raise ValueError("test error")
""")

        import sys
        sys.path.insert(0, str(tmpdir_path))

        try:
            config = TaskConfig(pyproject)
            executor = TaskExecutor(config)
            exit_code = executor.execute("pycall")
            assert exit_code == 1
            captured = capsys.readouterr()
            assert "Error executing Python call" in captured.err
        finally:
            sys.path.pop(0)
            if "testmodule5" in sys.modules:
                del sys.modules["testmodule5"]
