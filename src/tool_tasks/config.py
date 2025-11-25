"""Task configuration loader and parser."""

import sys
import tomllib
from pathlib import Path
from typing import Any


class TaskConfig:
    """Load and parse task configuration from pyproject.toml."""

    def __init__(self, config_path: Path | None = None):
        """
        Initialize TaskConfig.

        Args:
            config_path: Path to pyproject.toml. If None, searches upward from current directory.
        """
        self.config_path = config_path or self._find_pyproject()
        self.tasks = self._load_tasks()

    def _find_pyproject(self) -> Path:
        """Find pyproject.toml by searching upward from current directory."""
        current = Path.cwd()
        while current != current.parent:
            pyproject = current / "pyproject.toml"
            if pyproject.exists():
                return pyproject
            current = current.parent

        # Check root directory
        pyproject = current / "pyproject.toml"
        if pyproject.exists():
            return pyproject

        raise FileNotFoundError("pyproject.toml not found in current directory or any parent directory")

    def _load_tasks(self) -> dict[str, Any]:
        """Load tasks from pyproject.toml [tool.tasks] section."""
        try:
            with open(self.config_path, "rb") as f:
                data = tomllib.load(f)
        except Exception as e:
            print(f"Error reading {self.config_path}: {e}", file=sys.stderr)
            sys.exit(1)

        tasks = data.get("tool", {}).get("tasks", {})
        if not tasks:
            print(f"No [tool.tasks] section found in {self.config_path}", file=sys.stderr)
            sys.exit(1)

        return tasks

    def get_task(self, task_name: str) -> Any:
        """
        Get task configuration by name.

        Args:
            task_name: Name of the task to retrieve.

        Returns:
            Task configuration value.

        Raises:
            KeyError: If task is not found.
        """
        if task_name not in self.tasks:
            available = ", ".join(sorted(self.tasks.keys()))
            print(f"Task '{task_name}' not found. Available tasks: {available}", file=sys.stderr)
            sys.exit(1)
        return self.tasks[task_name]

    def list_tasks(self) -> list[str]:
        """Return list of available task names."""
        return sorted(self.tasks.keys())
