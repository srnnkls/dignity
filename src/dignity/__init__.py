"""CLI for Claude Code utilities.

Provides commands for:
- statusline: Generate status line for Claude Code
- tokens: Display token metrics from transcript
- dispatch: Process hook events with declarative rules
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Annotated, Literal

import typer

from dignity.statusline import StatusLineInput, render_statusline
from dignity.tokens import get_token_metrics

app = typer.Typer()

HookEventArg = Literal["UserPromptSubmit", "Stop", "SubagentStop"]


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
        # Format for status line: "In: X | Out: Y | Cache: Z | Total: W | Ctx: C"
        parts = [
            f"In: {format_number(metrics.input_tokens)}",
            f"Out: {format_number(metrics.output_tokens)}",
            f"Cache: {format_number(metrics.cached_tokens)}",
            f"Total: {format_number(metrics.total_tokens)}",
            f"Ctx: {format_number(metrics.context_length)}",
        ]
        print(" | ".join(parts))


@app.command(name="statusline")
def statusline_command() -> None:
    """Generate status line for Claude Code (reads JSON from stdin)."""
    input_json = json.load(sys.stdin)

    status_input = StatusLineInput(
        model_name=input_json.get("model", {}).get("display_name", "Unknown"),
        current_dir=input_json.get("workspace", {}).get("current_dir", ""),
        transcript_path=input_json.get("transcript_path", ""),
        max_tokens=input_json.get("budgetInfo", {}).get("tokenBudget", 200000),
    )

    print(render_statusline(status_input))


@app.command(name="dispatch")
def dispatch_command(
    hook_event: Annotated[
        str,
        typer.Argument(help="Hook event type: UserPromptSubmit, Stop, or SubagentStop"),
    ],
) -> None:
    """Process hook event with declarative dispatch rules.

    Reads JSON data from stdin and outputs appropriate response
    based on configured rules.

    Example:
        echo '{"prompt":"test"}' | dignity dispatch UserPromptSubmit
    """
    from dignity.hooks.dispatch import dispatch

    if hook_event not in ("UserPromptSubmit", "Stop", "SubagentStop"):
        typer.echo(f"Invalid hook event: {hook_event}", err=True)
        raise typer.Exit(1)

    data = json.load(sys.stdin)
    dispatch(hook_event, data)  # type: ignore[arg-type]


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    app()
