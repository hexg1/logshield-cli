from __future__ import annotations

import httpx
from prompt_toolkit import PromptSession
from prompt_toolkit.filters import is_done
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from logshield import __version__, config
from logshield.client import AuthError, LogShieldClient, LogShieldError, QuotaError

console = Console()

LOGO = r"""
  _                ____  _     _      _     _
 | |    ___   __ _/ ___|| |__ (_) ___| | __| |
 | |   / _ \ / _` \___ \| '_ \| |/ _ \ |/ _` |
 | |__| (_) | (_| |___) | | | | |  __/ | (_| |
 |_____\___/ \__, |____/|_| |_|_|\___|_|\__,_|
              |___/
"""

PROMPT_STYLE = Style.from_dict({
    "prompt": "#00afff bold",
    "slash": "#888888",
})


def _make_client() -> LogShieldClient | None:
    creds = config.load()
    if creds is None:
        return None
    return LogShieldClient(api_url=creds.api_url, api_host=creds.api_host, rapidapi_key=creds.rapidapi_key, local=creds.local)


def _print_banner() -> None:
    console.print(f"[bold cyan]{LOGO}[/bold cyan]")
    console.print(
        "  [dim]sanitize before you share[/dim]  "
        f"[dim]v{__version__}[/dim]\n"
    )
    console.print(
        "  [dim]🔒 Your data is never saved or shared[/dim]\n"
    )
    console.print(
        "  type text to sanitize  [dim]|[/dim]  "
        "[bold]/help[/bold] for commands\n"
    )


def _cmd_status() -> None:
    client = _make_client()
    if client is None:
        console.print("[yellow]Not configured.[/yellow] Run [bold]/setkey <your-rapidapi-key>[/bold] first.")
        return
    try:
        data = client.usage()
    except httpx.ConnectError:
        console.print("[red]x Cannot reach server.[/red] Check your connection.")
        return
    except LogShieldError as e:
        console.print(f"[red]x {e}[/red]")
        return
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_row("[cyan]Plan[/cyan]", data["plan"])
    table.add_row("[cyan]Calls[/cyan]", f"{data['calls_this_month']} / {data['limit']}")
    console.print(Panel(table, title="Status", border_style="cyan"))


def _cmd_setkey(key: str) -> None:
    if key == "local":
        config.save(config.local_credentials())
        console.print("[green]ok Local dev mode activated.[/green] Pointing to http://localhost:8000")
    else:
        config.save(config.Credentials(rapidapi_key=key))
        console.print("[green]ok API key saved.[/green]")


def _cmd_logout() -> None:
    if config.clear():
        console.print("[green]ok Key removed[/green]")
    else:
        console.print("[yellow]Not configured[/yellow]")


def _cmd_help() -> None:
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_row("[bold cyan]<text>[/bold cyan]", "Sanitize text and show detections")
    table.add_row("[bold cyan]/setkey <key>[/bold cyan]", "Set your RapidAPI key")
    table.add_row("[bold cyan]/status[/bold cyan]", "Show plan and quota usage")
    table.add_row("[bold cyan]/logout[/bold cyan]", "Remove saved API key")
    table.add_row("[bold cyan]/privacy[/bold cyan]", "Privacy & security info")
    table.add_row("[bold cyan]/help[/bold cyan]", "Show this help")
    table.add_row("[bold cyan]/exit[/bold cyan]", "Quit")
    console.print(Panel(table, title="Commands", border_style="cyan"))


def _cmd_privacy() -> None:
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_row("[green]✓[/green]", "Data is never saved to our servers")
    table.add_row("[green]✓[/green]", "No third-party access to your data")
    table.add_row("[green]✓[/green]", "Only API usage is logged (anonymously)")
    table.add_row("[green]✓[/green]", "HTTPS-only, no credentials stored")
    console.print(Panel(table, title="Privacy & Security", border_style="green"))


def _print_quota_warning(quota_pct: float) -> None:
    if quota_pct >= 95:
        console.print(f"\n[bold red]🔴 QUOTA AL {quota_pct:.0f}% — upgrade ora: rapidapi.com/logshield[/bold red]")
    elif quota_pct >= 80:
        console.print(f"\n[yellow]⚠  Quota all'{quota_pct:.0f}% — considera l'upgrade prima di esaurirla[/yellow]")


def _sanitize_text(text: str) -> None:
    client = _make_client()
    if client is None:
        console.print("[yellow]Not configured.[/yellow] Run [bold]/setkey <your-rapidapi-key>[/bold] first.")
        return
    try:
        with console.status("[cyan]Sanitizing...[/cyan]"):
            result = client.sanitize(text)
    except httpx.ConnectError:
        console.print("[red]x Cannot reach server.[/red] Check your connection.")
        return
    except AuthError:
        console.print("[red]x Invalid API key.[/red] Run [bold]/login[/bold].")
        return
    except QuotaError as e:
        console.print(f"[red]x {e}[/red]")
        return
    except LogShieldError as e:
        console.print(f"[red]x {e}[/red]")
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
    _print_quota_warning(result.quota_pct)


def _prompt_bottom() -> HTML:
    creds = config.load()
    if creds:
        right = f"<slash>{creds.email}</slash>"
    else:
        right = "<slash>not logged in</slash>"
    return HTML(f"<prompt>logshield</prompt><slash> > </slash>")


def _make_bindings() -> KeyBindings:
    kb = KeyBindings()

    @kb.add("enter")
    def _newline(event):
        event.current_buffer.insert_text("\n")

    @kb.add("escape", "enter")
    def _submit(event):
        event.current_buffer.validate_and_handle()

    return kb


def run_tui() -> None:
    _print_banner()
    console.print("  [dim]Enter[/dim] = new line  [dim]|[/dim]  [dim]Alt+Enter[/dim] = send\n")
    session: PromptSession = PromptSession(
        multiline=True,
        key_bindings=_make_bindings(),
    )

    while True:
        try:
            raw = session.prompt(
                HTML("<ansibrightcyan><b>logshield</b></ansibrightcyan><ansigray> > </ansigray>"),
            ).strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]bye[/dim]")
            break

        if not raw:
            continue

        if raw.startswith("/"):
            parts = raw.lstrip("/").split()
            cmd = parts[0].lower()
            if cmd == "exit":
                console.print("[dim]bye[/dim]")
                break
            elif cmd == "help":
                _cmd_help()
            elif cmd == "status":
                _cmd_status()
            elif cmd == "setkey":
                if len(parts) < 2:
                    console.print("[yellow]Usage:[/yellow] /setkey <your-rapidapi-key>")
                else:
                    _cmd_setkey(parts[1])
            elif cmd == "logout":
                _cmd_logout()
            elif cmd == "privacy":
                _cmd_privacy()
            else:
                console.print(f"[yellow]Unknown command:[/yellow] /{cmd}  (try [bold]/help[/bold])")
        else:
            _sanitize_text(raw)
