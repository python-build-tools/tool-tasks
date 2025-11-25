"""CLI entry point for the task command."""

import sys
from pathlib import Path

from tool_tasks.config import TaskConfig
from tool_tasks.executor import TaskExecutor


def main():
    """Main entry point for the task CLI."""
    # Parse command-line arguments
    if len(sys.argv) < 2:
        print("Usage: task <task-name> [args...]", file=sys.stderr)
        print("       task --list", file=sys.stderr)
        sys.exit(1)

    # Handle --list option
    if sys.argv[1] == "--list":
        try:
            config = TaskConfig()
            tasks = config.list_tasks()
            if tasks:
                print("Available tasks:")
                for task in tasks:
                    print(f"  {task}")
            else:
                print("No tasks defined in [tool.tasks]")
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        return

    # Get task name and arguments
    task_name = sys.argv[1]
    task_args = sys.argv[2:]

    # Load configuration and execute task
    try:
        config = TaskConfig()
        executor = TaskExecutor(config)
        exit_code = executor.execute(task_name, task_args)
        sys.exit(exit_code)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
