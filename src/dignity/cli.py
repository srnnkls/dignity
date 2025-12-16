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
app.add_typer(spec_app, name="spec", help="Spec management commands")


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


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    app()
