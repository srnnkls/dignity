"""CLI for Claude Code utilities."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Annotated

import typer

from dignity.statusline import StatusLineInput, render_statusline
from dignity.tokens import get_token_metrics

app = typer.Typer()
spec_app = typer.Typer()
task_app = typer.Typer()
app.add_typer(spec_app, name="spec", help="Spec management commands")
spec_app.add_typer(task_app, name="task", help="Task management commands")


def format_number(n: int) -> str:
    """Format a number with K/M suffix for readability."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


@app.command()
def tokens(
    transcript_file: Annotated[
        Path, typer.Argument(help="Path to the Claude Code transcript JSONL file")
    ],
    output: Annotated[
        str, typer.Option("--output", "-o", help="Output format: text or json")
    ] = "text",
) -> None:
    """Display token metrics from Claude Code transcript."""
    metrics = get_token_metrics(transcript_file)

    if output == "json":
        print(
            json.dumps(
                {
                    "input_tokens": metrics.input_tokens,
                    "output_tokens": metrics.output_tokens,
                    "cached_tokens": metrics.cached_tokens,
                    "total_tokens": metrics.total_tokens,
                    "context_length": metrics.context_length,
                }
            )
        )
    else:
        parts = [
            f"In: {format_number(metrics.input_tokens)}",
            f"Out: {format_number(metrics.output_tokens)}",
            f"Cache: {format_number(metrics.cached_tokens)}",
            f"Total: {format_number(metrics.total_tokens)}",
            f"Ctx: {format_number(metrics.context_length)}",
        ]
        print(" | ".join(parts))


@app.command()
def status() -> None:
    """Generate status line for Claude Code (reads JSON from stdin)."""
    try:
        input_json = json.load(sys.stdin)
        status_input = StatusLineInput(
            model_name=input_json.get("model", {}).get("display_name", "Unknown"),
            current_dir=input_json.get("workspace", {}).get("current_dir", ""),
            transcript_path=input_json.get("transcript_path", ""),
            max_tokens=input_json.get("budgetInfo", {}).get("tokenBudget", 200000),
        )
        print(render_statusline(status_input))
    except Exception as e:
        print(f"status error: {e}", file=sys.stderr)
        raise typer.Exit(1)


@spec_app.command("create")
def spec_create(
    spec_name: Annotated[str, typer.Argument(help="Spec name in kebab-case")],
    issue_type: Annotated[
        str, typer.Option("--type", "-t", help="Issue type: feature, bug, or chore")
    ] = "feature",
    no_register: Annotated[
        bool, typer.Option("--no-register", help="Skip adding to index.yaml")
    ] = False,
) -> None:
    """Create a new spec with scaffolded files.

    Example:
        dignity spec create my-feature --type feature
    """
    from dignity.spec import SpecCreateError, create

    try:
        config = create(spec_name, issue_type=issue_type, register=not no_register)
        typer.echo(f"Created spec '{config.name}' with code {config.code}")
        typer.echo(f"  → specs/active/{config.name}/spec.md")
        typer.echo(f"  → specs/active/{config.name}/context.md")
        typer.echo(f"  → specs/active/{config.name}/tasks.yaml")
        typer.echo(f"  → specs/active/{config.name}/dependencies.md")
        typer.echo(f"  → specs/active/{config.name}/validation-checklist.md")
        if not no_register:
            typer.echo(f"  → specs/index.yaml ({config.code}: {config.name})")
    except SpecCreateError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1)


@task_app.command("add")
def task_add(
    spec_path: Annotated[Path, typer.Argument(help="Path to spec directory")],
    content: Annotated[str | None, typer.Argument(help="Task description")] = None,
    active_form: Annotated[str | None, typer.Argument(help="Active form of task description")] = None,
    use_json: Annotated[bool, typer.Option("--json", help="Read task(s) from JSON stdin")] = False,
) -> None:
    """Add a new task to a spec."""
    from dignity.spec import SpecNotFoundError, add_task, add_tasks, load_tasks, save_tasks
    from dignity.spec.types import Status, Task, TasksFile

    if use_json:
        try:
            input_data = json.load(sys.stdin)
        except json.JSONDecodeError as e:
            typer.echo(f"Error: Invalid JSON - {e}")
            raise typer.Exit(1)

        try:
            if "todos" in input_data:
                tasks_to_add = input_data["todos"]
            else:
                tasks_to_add = [input_data]

            if not tasks_to_add:
                typer.echo("No tasks to add")
                return

            for task_dict in tasks_to_add:
                if "content" not in task_dict:
                    typer.echo("Error: Missing 'content' field in task")
                    raise typer.Exit(1)
                if "activeForm" not in task_dict:
                    typer.echo("Error: Missing 'activeForm' field in task")
                    raise typer.Exit(1)

            tasks_file = load_tasks(spec_path)
            added_tasks = []

            for task_dict in tasks_to_add:
                status_str = task_dict.get("status", "pending")
                status = Status(status_str)
                task_id = f"{tasks_file.code}-{tasks_file.next_id:03d}"
                task = Task(
                    id=task_id,
                    content=task_dict["content"],
                    status=status,
                    active_form=task_dict["activeForm"],
                )
                tasks_file.tasks.append(task)
                tasks_file.next_id += 1
                added_tasks.append(task)

            save_tasks(spec_path, tasks_file)

            for task in added_tasks:
                typer.echo(f"Added task {task.id}: {task.content}")

        except (FileNotFoundError, SpecNotFoundError):
            typer.echo(f"Error: Spec not found at {spec_path}")
            raise typer.Exit(1)
    else:
        if content is None or active_form is None:
            typer.echo("Error: content and active_form are required when not using --json")
            raise typer.Exit(1)

        try:
            task = add_task(spec_path, content, active_form)
            typer.echo(f"Added task {task.id}: {task.content}")
        except (FileNotFoundError, SpecNotFoundError):
            typer.echo(f"Error: Spec not found at {spec_path}")
            raise typer.Exit(1)


@task_app.command("complete")
def task_complete(
    spec_path: Annotated[Path, typer.Argument(help="Path to spec directory")],
    task_id: Annotated[str, typer.Argument(help="Task ID to complete")],
) -> None:
    """Mark a task as completed."""
    from dignity.spec import TaskNotFoundError, complete_task

    try:
        task = complete_task(spec_path, task_id)
        typer.echo(f"Completed task {task.id}: {task.content}")
    except TaskNotFoundError:
        typer.echo(f"Error: Task {task_id} not found")
        raise typer.Exit(1)
    except FileNotFoundError:
        typer.echo(f"Error: Spec not found at {spec_path}")
        raise typer.Exit(1)


@task_app.command("start")
def task_start(
    spec_path: Annotated[Path, typer.Argument(help="Path to spec directory")],
    task_id: Annotated[str, typer.Argument(help="Task ID to start")],
) -> None:
    """Mark a task as in_progress."""
    from dignity.spec import TaskNotFoundError, start_task

    try:
        task = start_task(spec_path, task_id)
        typer.echo(f"Started task {task.id} (in_progress): {task.content}")
    except TaskNotFoundError:
        typer.echo(f"Error: Task {task_id} not found")
        raise typer.Exit(1)
    except FileNotFoundError:
        typer.echo(f"Error: Spec not found at {spec_path}")
        raise typer.Exit(1)


@task_app.command("discard")
def task_discard(
    spec_path: Annotated[Path, typer.Argument(help="Path to spec directory")],
    task_id: Annotated[str, typer.Argument(help="Task ID to discard")],
) -> None:
    """Discard (remove) a task."""
    from dignity.spec import TaskNotFoundError, discard_task

    try:
        discard_task(spec_path, task_id)
        typer.echo(f"Discarded task {task_id}")
    except TaskNotFoundError:
        typer.echo(f"Error: Task {task_id} not found")
        raise typer.Exit(1)
    except FileNotFoundError:
        typer.echo(f"Error: Spec not found at {spec_path}")
        raise typer.Exit(1)


@task_app.command("list")
def task_list(
    spec_path: Annotated[Path, typer.Argument(help="Path to spec directory")],
) -> None:
    """List all tasks in a spec."""
    from dignity.spec import load_tasks

    try:
        tasks_file = load_tasks(spec_path)
        if not tasks_file.tasks:
            typer.echo("No tasks found")
            return
        for task in tasks_file.tasks:
            typer.echo(f"{task.id}: {task.content} [{task.status.value}]")
    except FileNotFoundError:
        typer.echo(f"Error: Spec not found at {spec_path}")
        raise typer.Exit(1)


@task_app.command("update")
def task_update(
    spec_path: Annotated[Path, typer.Argument(help="Path to spec directory")],
    task_id: Annotated[str, typer.Argument(help="Task ID to update or create")],
    content: Annotated[str | None, typer.Option("--content", help="Task content")] = None,
    active_form: Annotated[str | None, typer.Option("--active-form", help="Active form")] = None,
    status: Annotated[str | None, typer.Option("--status", help="Status (pending, in_progress, completed)")] = None,
    use_json: Annotated[bool, typer.Option("--json", help="Read fields from JSON stdin")] = False,
) -> None:
    """Update or create a task (upsert). Creates if ID doesn't exist."""
    from dignity.spec import update_task
    from dignity.spec.types import Status

    if use_json:
        try:
            input_data = json.load(sys.stdin)
        except json.JSONDecodeError as e:
            typer.echo(f"Error: Invalid JSON - {e}")
            raise typer.Exit(1)

        content = input_data.get("content", content)
        active_form = input_data.get("activeForm", active_form)
        status = input_data.get("status", status)

    status_enum = None
    if status is not None:
        try:
            status_enum = Status(status)
        except ValueError:
            typer.echo(f"Error: Invalid status '{status}'. Must be pending, in_progress, or completed.")
            raise typer.Exit(1)

    try:
        task, created = update_task(spec_path, task_id, content=content, active_form=active_form, status=status_enum)
        action = "Created" if created else "Updated"
        typer.echo(f"{action} task {task.id}: {task.content}")
    except ValueError as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(1)
    except FileNotFoundError:
        typer.echo(f"Error: Spec not found at {spec_path}")
        raise typer.Exit(1)


@task_app.command("sync")
def task_sync(
    spec_path: Annotated[Path, typer.Argument(help="Path to spec directory")],
    use_json: Annotated[bool, typer.Option("--json", help="Read tasks from JSON stdin")] = False,
) -> None:
    """Sync tasks - replace entire task list with new tasks from JSON."""
    from dignity.spec import SpecNotFoundError, load_tasks, save_tasks
    from dignity.spec.types import Status, Task, TasksFile

    if not use_json:
        typer.echo("Error: --json flag is required for sync command")
        raise typer.Exit(1)

    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        typer.echo(f"Error: Invalid JSON - {e}")
        raise typer.Exit(1)

    if "todos" not in input_data:
        typer.echo("Error: Missing 'todos' key in JSON")
        raise typer.Exit(1)

    try:
        tasks_file = load_tasks(spec_path)
    except FileNotFoundError:
        typer.echo(f"Error: Spec not found at {spec_path}")
        raise typer.Exit(1)

    todos = input_data["todos"]
    new_tasks = []

    for i, task_dict in enumerate(todos, start=1):
        status_str = task_dict.get("status", "pending")
        status = Status(status_str)
        task_id = f"{tasks_file.code}-{i:03d}"
        task = Task(
            id=task_id,
            content=task_dict["content"],
            status=status,
            active_form=task_dict["activeForm"],
        )
        new_tasks.append(task)

    tasks_file.tasks = new_tasks
    tasks_file.next_id = len(new_tasks) + 1
    save_tasks(spec_path, tasks_file)

    typer.echo(f"Synced {len(new_tasks)} tasks")


@spec_app.command("archive")
def spec_archive(
    spec_path: Annotated[Path, typer.Argument(help="Path to spec directory to archive")],
) -> None:
    """Archive a spec (move from active to archive)."""
    from dignity.spec import SpecNotFoundError, archive

    try:
        dest = archive(spec_path)
        typer.echo(f"Archived spec to {dest}")
    except SpecNotFoundError:
        typer.echo(f"Error: Spec not found at {spec_path}")
        raise typer.Exit(1)
    except ValueError as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(1)


@spec_app.command("restore")
def spec_restore(
    spec_path: Annotated[Path, typer.Argument(help="Path to archived spec to restore")],
) -> None:
    """Restore an archived spec (move from archive to active)."""
    from dignity.spec import SpecNotFoundError, restore

    try:
        dest = restore(spec_path)
        typer.echo(f"Restored spec to {dest}")
    except SpecNotFoundError:
        typer.echo(f"Error: Spec not found at {spec_path}")
        raise typer.Exit(1)
    except ValueError as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(1)


@spec_app.command("list")
def spec_list(
    base: Annotated[
        Path | None, typer.Option("--base", help="Base specs directory")
    ] = None,
    status: Annotated[
        str | None, typer.Option("--status", help="Filter by status (Active, Archived)")
    ] = None,
) -> None:
    """List all specs."""
    from dignity.spec import list_specs

    base_path = base if base else Path("specs")
    specs = list_specs(base_path, status=status)
    if not specs:
        typer.echo("No specs found")
        return
    for spec in specs:
        typer.echo(f"{spec.code}: {spec.name} [{spec.status}]")


@spec_app.command("show")
def spec_show(
    spec_path: Annotated[Path, typer.Argument(help="Path to spec directory")],
) -> None:
    """Show details of a spec."""
    from dignity.spec import SpecNotFoundError, get_spec

    try:
        spec = get_spec(spec_path)
        typer.echo(f"Name: {spec.name}")
        typer.echo(f"Code: {spec.code}")
        typer.echo(f"Type: {spec.issue_type}")
        typer.echo(f"Status: {spec.status}")
        typer.echo(f"Created: {spec.created.isoformat()}")
    except SpecNotFoundError:
        typer.echo(f"Error: Spec not found at {spec_path}")
        raise typer.Exit(1)


@spec_app.command("progress")
def spec_progress(
    spec_path: Annotated[Path, typer.Argument(help="Path to spec directory")],
) -> None:
    """Show progress of a spec."""
    from dignity.spec import SpecNotFoundError, get_progress

    try:
        progress = get_progress(spec_path)
        typer.echo(f"Total: {progress['total']}")
        typer.echo(f"Completed: {progress['completed']}")
        typer.echo(f"In_progress: {progress['in_progress']}")
        typer.echo(f"Pending: {progress['pending']}")
        typer.echo(f"Progress: {progress['percent_complete']:.0f}%")
    except SpecNotFoundError:
        typer.echo(f"Error: Spec not found at {spec_path}")
        raise typer.Exit(1)


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    app()
