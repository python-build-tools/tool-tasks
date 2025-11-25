"""Task executor for running different types of tasks."""

import importlib
import subprocess
import sys
from typing import Any


class TaskExecutor:
    """Execute different types of tasks."""

    def __init__(self, config):
        """
        Initialize TaskExecutor.

        Args:
            config: TaskConfig instance.
        """
        self.config = config
        self._executing = set()  # Track tasks being executed to detect circular dependencies

    def execute(self, task_name: str, args: list[str] | None = None) -> int:
        """
        Execute a task by name.

        Args:
            task_name: Name of the task to execute.
            args: Additional arguments to pass to the task.

        Returns:
            Exit code from the task execution.
        """
        if task_name in self._executing:
            print(f"Circular dependency detected: task '{task_name}' is already being executed", file=sys.stderr)
            return 1

        self._executing.add(task_name)
        try:
            task_config = self.config.get_task(task_name)
            return self._execute_task(task_config, args or [], current_task=task_name)
        finally:
            self._executing.discard(task_name)

    def _execute_task(self, task_config: Any, args: list[str], current_task: str = "") -> int:
        """
        Execute a task based on its configuration.

        Args:
            task_config: Task configuration value.
            args: Additional arguments to pass to the task.
            current_task: The name of the current task being executed.

        Returns:
            Exit code from the task execution.
        """
        # Handle different task types
        if isinstance(task_config, str):
            return self._execute_string_task(task_config, args, current_task)
        elif isinstance(task_config, list):
            return self._execute_chain(task_config, args, current_task)
        elif isinstance(task_config, dict):
            return self._execute_dict_task(task_config, args, current_task)
        else:
            print(f"Invalid task configuration type: {type(task_config)}", file=sys.stderr)
            return 1

    def _execute_string_task(self, task_config: str, args: list[str], current_task: str = "") -> int:
        """
        Execute a string task (shell command or task alias).

        Args:
            task_config: String task configuration.
            args: Additional arguments to pass to the task.
            current_task: The name of the current task being executed.

        Returns:
            Exit code from the task execution.
        """
        # Check if it's a task alias (references another task)
        # But not if it references itself (to avoid infinite loops)
        if task_config in self.config.tasks and task_config != current_task:
            return self.execute(task_config, args)

        # Otherwise, treat as shell command
        return self._execute_shell(task_config, args)

    def _execute_chain(self, task_config: list[str], args: list[str], current_task: str = "") -> int:
        """
        Execute a chain of tasks.

        Args:
            task_config: List of task names to execute in sequence.
            args: Additional arguments (passed to each task in chain).
            current_task: The name of the current task being executed.

        Returns:
            Exit code from the first failing task, or 0 if all succeed.
        """
        for task in task_config:
            exit_code = self._execute_string_task(task, args, current_task)
            if exit_code != 0:
                return exit_code
        return 0

    def _execute_dict_task(self, task_config: dict, args: list[str], current_task: str = "") -> int:
        """
        Execute a dictionary-configured task.

        Args:
            task_config: Dictionary task configuration.
            args: Additional arguments to pass to the task.
            current_task: The name of the current task being executed.

        Returns:
            Exit code from the task execution.
        """
        # Check for 'cmd' key (shell command)
        if "cmd" in task_config:
            return self._execute_shell(task_config["cmd"], args)

        # Check for 'call' key (Python module entry point)
        if "call" in task_config:
            return self._execute_python_call(task_config["call"], args)

        # Check for 'chain' key (task chain)
        if "chain" in task_config:
            return self._execute_chain(task_config["chain"], args, current_task)

        print(f"Invalid task configuration: {task_config}", file=sys.stderr)
        return 1

    def _execute_shell(self, command: str, args: list[str]) -> int:
        """
        Execute a shell command.

        Args:
            command: Shell command to execute.
            args: Additional arguments to append to the command.

        Returns:
            Exit code from the shell command.
        """
        # Append additional arguments to the command
        if args:
            command = f"{command} {' '.join(args)}"

        try:
            result = subprocess.run(command, shell=True, cwd=self.config.config_path.parent)
            return result.returncode
        except Exception as e:
            print(f"Error executing shell command: {e}", file=sys.stderr)
            return 1

    def _execute_python_call(self, module_path: str, args: list[str]) -> int:
        """
        Execute a Python module entry point.

        Args:
            module_path: Module path in format 'module.path:function' or 'module.path:Class.method'.
            args: Additional arguments to pass to the function/method.

        Returns:
            Exit code from the Python call.
        """
        try:
            # Parse module path
            if ":" not in module_path:
                print(f"Invalid call format: {module_path}. Expected 'module:function'", file=sys.stderr)
                return 1

            module_name, func_path = module_path.split(":", 1)

            # Import the module
            try:
                module = importlib.import_module(module_name)
            except ImportError as e:
                print(f"Failed to import module '{module_name}': {e}", file=sys.stderr)
                return 1

            # Get the function/method
            obj = module
            for attr in func_path.split("."):
                try:
                    obj = getattr(obj, attr)
                except AttributeError:
                    print(f"'{attr}' not found in {obj}", file=sys.stderr)
                    return 1

            # Call the function/method with arguments
            # Set sys.argv for the called function
            old_argv = sys.argv
            sys.argv = [module_path] + args
            try:
                result = obj()
                # Handle different return types
                if result is None:
                    return 0
                elif isinstance(result, int):
                    return result
                else:
                    return 0
            finally:
                sys.argv = old_argv

        except Exception as e:
            print(f"Error executing Python call: {e}", file=sys.stderr)
            return 1
