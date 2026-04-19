from __future__ import annotations

import sys

import httpx
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from logshield import __version__, config
from logshield.client import AuthError, LogShieldClient, LogShieldError, QuotaError

app = typer.Typer(
    name="logshield",
    help="Sanitize text before sending to LLMs. Run `logshield setkey` to start.",
    no_args_is_help=False,
    add_completion=False,
)
console = Console()


def _get_client() -> LogShieldClient:
    creds = config.load()
    if creds is None:
        console.print("[red]Not configured.[/red] Run [bold]logshield setkey[/bold] first.")
        raise typer.Exit(code=1)
    return LogShieldClient(api_url=creds.api_url, api_host=creds.api_host, rapidapi_key=creds.rapidapi_key, local=creds.local)


@app.command(help="Set your RapidAPI key.")
def setkey(
    key: str = typer.Argument(..., help="Your RapidAPI key"),
) -> None:
    config.save(config.Credentials(rapidapi_key=key))
    console.print("[green]ok API key saved.[/green]")


@app.command(help="Clear saved credentials.")
def logout() -> None:
    if config.clear():
        console.print("[green]ok Logged out[/green]")
    else:
        console.print("[yellow]Not configured[/yellow]")


@app.command(help="Show current plan and quota usage.")
def status() -> None:
    client = _get_client()
    try:
        data = client.usage()
    except httpx.ConnectError:
        console.print("[red]x Cannot reach server.[/red] Check your connection or try later.")
        raise typer.Exit(code=1) from None
    except LogShieldError as e:
        console.print(f"[red]x {e}[/red]")
        raise typer.Exit(code=1) from None

    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_row("[cyan]Plan[/cyan]", data["plan"])
    table.add_row(
        "[cyan]Calls this month[/cyan]",
        f"{data['calls_this_month']} / {data['limit']}",
    )
    console.print(Panel(table, title="LogShield Status", border_style="cyan"))


@app.command(help="Sanitize text and print result.", name="sanitize")
def sanitize_cmd(
    text: str = typer.Argument(None, help="Text to sanitize. If omitted, reads stdin."),
    confidence: int = typer.Option(80, "--confidence", "-c", min=0, max=100),
    raw: bool = typer.Option(False, "--raw", help="Print only sanitized text, no summary"),
) -> None:
    if text is None:
        if sys.stdin.isatty():
            console.print("[yellow]No text provided. Pipe stdin or pass argument.[/yellow]")
            raise typer.Exit(code=1)
        text = sys.stdin.read()

    client = _get_client()
    try:
        result = client.sanitize(text, confidence_threshold=confidence)
    except httpx.ConnectError:
        console.print("[red]x Cannot reach server.[/red] Check your connection or try later.")
        raise typer.Exit(code=1) from None
    except AuthError:
        console.print("[red]x Invalid RapidAPI key.[/red] Run [bold]logshield setkey <key>[/bold].")
        raise typer.Exit(code=1) from None
    except QuotaError as e:
        console.print(f"[red]x {e}[/red]")
        raise typer.Exit(code=2) from None
    except LogShieldError as e:
        console.print(f"[red]x {e}[/red]")
        raise typer.Exit(code=1) from None

    if raw:
        sys.stdout.write(result.sanitized_text)
        return

    console.print(Panel(result.sanitized_text, title="Sanitized", border_style="green"))
    if result.detections:
        table = Table(title=f"Detections ({len(result.detections)})", show_lines=False)
        table.add_column("Pattern", style="cyan")
        table.add_column("Confidence", style="magenta")
        table.add_column("Placeholder", style="yellow")
        for d in result.detections:
            table.add_row(d["pattern"], f"{d['confidence']}%", d["placeholder"])
        console.print(table)
    console.print(f"[dim]Processed in {result.processing_ms:.2f} ms[/dim]")


@app.command(help="Show version.")
def version() -> None:
    console.print(f"logshield [bold]{__version__}[/bold]")


_KNOWN = {"setkey", "logout", "status", "sanitize", "version", "--help", "-h"}


def run() -> None:
    if len(sys.argv) <= 1:
        from logshield.tui import run_tui
        run_tui()
        return
    first = sys.argv[1]
    if first not in _KNOWN and not first.startswith("-"):
        sys.argv.insert(1, "sanitize")
    app()


if __name__ == "__main__":
    run()
