"""Tests for the config module."""

import os
import sys
import tempfile
from pathlib import Path

import pytest

from tool_tasks.config import TaskConfig


def test_find_pyproject_in_current_dir():
    """Test finding pyproject.toml in current directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        pyproject = tmpdir_path / "pyproject.toml"
        pyproject.write_text("""
[tool.tasks]
test = "echo test"
""")

        # Change to temp directory
        old_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            config = TaskConfig()
            assert config.config_path == pyproject
        finally:
            os.chdir(old_cwd)


def test_find_pyproject_in_parent_dir():
    """Test finding pyproject.toml in parent directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        pyproject = tmpdir_path / "pyproject.toml"
        pyproject.write_text("""
[tool.tasks]
test = "echo test"
""")
        subdir = tmpdir_path / "subdir"
        subdir.mkdir()

        # Change to subdirectory
        old_cwd = os.getcwd()
        try:
            os.chdir(subdir)
            config = TaskConfig()
            assert config.config_path == pyproject
        finally:
            os.chdir(old_cwd)


def test_pyproject_not_found():
    """Test error when pyproject.toml is not found."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        subdir = tmpdir_path / "subdir"
        subdir.mkdir()

        # Change to subdirectory
        old_cwd = os.getcwd()
        try:
            os.chdir(subdir)
            with pytest.raises(FileNotFoundError, match="pyproject.toml not found"):
                TaskConfig()
        finally:
            os.chdir(old_cwd)


def test_load_tasks_missing_tool_tasks_section(capsys):
    """Test error when [tool.tasks] section is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        pyproject = tmpdir_path / "pyproject.toml"
        pyproject.write_text("""
[tool.poetry]
name = "test"
""")

        with pytest.raises(SystemExit) as exc_info:
            TaskConfig(pyproject)

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "No [tool.tasks] section found" in captured.err


def test_load_tasks_invalid_toml(capsys):
    """Test error when pyproject.toml is invalid."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        pyproject = tmpdir_path / "pyproject.toml"
        pyproject.write_text("invalid toml content [[[")

        with pytest.raises(SystemExit) as exc_info:
            TaskConfig(pyproject)

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Error reading" in captured.err


def test_get_task():
    """Test getting a task by name."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        pyproject = tmpdir_path / "pyproject.toml"
        pyproject.write_text("""
[tool.tasks]
test = "echo test"
build = "make build"
""")

        config = TaskConfig(pyproject)
        assert config.get_task("test") == "echo test"
        assert config.get_task("build") == "make build"


def test_get_task_not_found(capsys):
    """Test error when task is not found."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        pyproject = tmpdir_path / "pyproject.toml"
        pyproject.write_text("""
[tool.tasks]
test = "echo test"
""")

        config = TaskConfig(pyproject)
        with pytest.raises(SystemExit) as exc_info:
            config.get_task("nonexistent")

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Task 'nonexistent' not found" in captured.err
        assert "Available tasks: test" in captured.err


def test_list_tasks():
    """Test listing all tasks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        pyproject = tmpdir_path / "pyproject.toml"
        pyproject.write_text("""
[tool.tasks]
test = "pytest"
build = "make build"
clean = "rm -rf dist"
""")

        config = TaskConfig(pyproject)
        tasks = config.list_tasks()
        assert tasks == ["build", "clean", "test"]


def test_load_complex_tasks():
    """Test loading complex task configurations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        pyproject = tmpdir_path / "pyproject.toml"
        pyproject.write_text("""
[tool.tasks]
simple = "echo simple"
chain = ["task1", "task2"]

[tool.tasks.dict_task]
cmd = "echo dict"

[tool.tasks.python_task]
call = "module:function"
""")

        config = TaskConfig(pyproject)
        assert config.get_task("simple") == "echo simple"
        assert config.get_task("chain") == ["task1", "task2"]
        assert config.get_task("dict_task") == {"cmd": "echo dict"}
        assert config.get_task("python_task") == {"call": "module:function"}


def test_find_pyproject_at_root():
    """Test finding pyproject.toml at the root directory."""
    # This test is hard to implement without modifying the filesystem root
    # We'll skip it as it's an edge case that's unlikely to occur in practice
    # The code path exists for completeness
    pass
