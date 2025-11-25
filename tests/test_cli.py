"""Tests for the CLI module."""

import sys
import tempfile
from pathlib import Path

import pytest

from tool_tasks.cli import main


def test_cli_no_arguments(monkeypatch, capsys):
    """Test CLI with no arguments."""
    monkeypatch.setattr(sys, "argv", ["task"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Usage: task <task-name>" in captured.err


def test_cli_list_tasks(monkeypatch, capsys):
    """Test CLI --list option."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        pyproject = tmpdir_path / "pyproject.toml"
        pyproject.write_text("""
[tool.tasks]
test = "echo test"
build = "make build"
clean = "rm -rf dist"
""")

        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            monkeypatch.setattr(sys, "argv", ["task", "--list"])
            main()

            captured = capsys.readouterr()
            assert "Available tasks:" in captured.out
            assert "build" in captured.out
            assert "clean" in captured.out
            assert "test" in captured.out
        finally:
            os.chdir(old_cwd)


def test_cli_list_tasks_no_pyproject(monkeypatch, capsys):
    """Test CLI --list when pyproject.toml not found."""
    with tempfile.TemporaryDirectory() as tmpdir:
        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            monkeypatch.setattr(sys, "argv", ["task", "--list"])

            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "pyproject.toml not found" in captured.err
        finally:
            os.chdir(old_cwd)


def test_cli_execute_task(monkeypatch):
    """Test CLI executing a task."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        pyproject = tmpdir_path / "pyproject.toml"
        pyproject.write_text("""
[tool.tasks]
hello = "echo hello"
""")

        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            monkeypatch.setattr(sys, "argv", ["task", "hello"])

            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 0
        finally:
            os.chdir(old_cwd)


def test_cli_execute_task_with_args(monkeypatch):
    """Test CLI executing a task with arguments."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        pyproject = tmpdir_path / "pyproject.toml"
        pyproject.write_text("""
[tool.tasks]
echo = "echo"
""")

        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            monkeypatch.setattr(sys, "argv", ["task", "echo", "hello", "world"])

            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 0
        finally:
            os.chdir(old_cwd)


def test_cli_execute_nonexistent_task(monkeypatch, capsys):
    """Test CLI executing a non-existent task."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        pyproject = tmpdir_path / "pyproject.toml"
        pyproject.write_text("""
[tool.tasks]
test = "echo test"
""")

        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            monkeypatch.setattr(sys, "argv", ["task", "nonexistent"])

            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "Task 'nonexistent' not found" in captured.err
        finally:
            os.chdir(old_cwd)


def test_cli_no_pyproject(monkeypatch, capsys):
    """Test CLI when pyproject.toml not found."""
    with tempfile.TemporaryDirectory() as tmpdir:
        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            monkeypatch.setattr(sys, "argv", ["task", "test"])

            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "pyproject.toml not found" in captured.err
        finally:
            os.chdir(old_cwd)


def test_cli_list_empty_tasks(monkeypatch, capsys):
    """Test CLI --list with no tasks defined."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        pyproject = tmpdir_path / "pyproject.toml"
        pyproject.write_text("""
[tool.poetry]
name = "test"
""")

        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            monkeypatch.setattr(sys, "argv", ["task", "--list"])

            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1
        finally:
            os.chdir(old_cwd)


def test_cli_unexpected_error(monkeypatch, capsys):
    """Test CLI with an unexpected error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        pyproject = tmpdir_path / "pyproject.toml"
        # Create an invalid config that will cause an unexpected error
        pyproject.write_text("""
[tool.tasks]
test = "echo test"
""")

        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            monkeypatch.setattr(sys, "argv", ["task", "test"])

            # Mock TaskConfig to raise an unexpected exception
            from tool_tasks import config
            original_init = config.TaskConfig.__init__

            def mock_init(self, config_path=None):
                raise RuntimeError("Unexpected error")

            monkeypatch.setattr(config.TaskConfig, "__init__", mock_init)

            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "Unexpected error" in captured.err
        finally:
            os.chdir(old_cwd)
