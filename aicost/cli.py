import warnings
# Suppress the urllib3 NotOpenSSLWarning on macOS/LibreSSL systems
warnings.filterwarnings("ignore", message=".*urllib3 v2 only supports OpenSSL 1.1.1+.*")

import json
from typing import List, Optional
import urllib.parse
import webbrowser

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from aicost import __version__
from aicost.calculator import (
    calculate_cost_breakdown,
    estimate_monthly_cost,
    fetch_remote_pricing,
    filter_models,
    format_unit_label,
    get_effective_rates,
    get_model_by_id,
    get_pricing_metadata,
    suggest_similar_models,
)
from aicost.currency import get_currency_date, get_exchange_rate, refresh_rates
from aicost.recommender import recommend_models

app = typer.Typer(
    help="AI-Cost-CLI: Calculate, Compare, Estimate, and Recommend AI API Costs.",
    no_args_is_help=True,
)
console = Console()


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"aicost-cli v{__version__}")
        raise typer.Exit()


@app.callback()
def main_callback(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=_version_callback,
        is_eager=True,
        help="Show the AI-Cost-CLI version and exit.",
    )
) -> None:
    """AI-Cost-CLI root command."""


def _print_json(payload: dict) -> None:
    # Print raw JSON via standard print so piping to jq / scripts has no Rich line wrapping
    print(json.dumps(payload, indent=2))


def _handle_missing_model(model_id: str, as_json: bool = False) -> None:
    suggestions = suggest_similar_models(model_id)
    if as_json:
        _print_json({
            "error": f"Model '{model_id}' not found in database.",
            "suggestions": suggestions,
        })
    else:
        hint = f" Did you mean: [cyan]{', '.join(suggestions)}[/cyan]?" if suggestions else ""
        console.print(f"[bold red]Error:[/bold red] Model '{model_id}' not found in database.{hint}")
    raise typer.Exit(1)


def _format_context_window(ctx: Optional[int]) -> str:
    if not ctx:
        return "-"
    if ctx >= 1_000_000:
        val = ctx / 1_000_000
        return f"{val:g}M"
    return f"{ctx // 1_000}K"


@app.command(name="list")
def list_models(
    currency: str = typer.Option("USD", "--currency", "-c", help="Target currency (e.g., USD, TRY, EUR)"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Filter by provider (e.g., OpenAI, Google)"),
    model_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by type (text, image, video, audio, gateway)"),
    tag: Optional[str] = typer.Option(None, "--tag", help="Filter by capability tag (e.g., coding, cheap, agentic)"),
    sort_by: Optional[str] = typer.Option(None, "--sort", "-s", help="Sort by: id, provider, input, output"),
    hide_legacy: bool = typer.Option(False, "--hide-legacy", help="Hide legacy/superseded models"),
    as_json: bool = typer.Option(False, "--json", help="Output structured JSON"),
) -> None:
    """Lists available AI models and their effective pricing."""
    models = filter_models(
        provider=provider,
        model_type=model_type,
        tag=tag,
        include_legacy=not hide_legacy,
        sort_by=sort_by,
    )
    meta = get_pricing_metadata()
    rate, curr = get_exchange_rate(currency)
    currency_date = get_currency_date()

    if as_json:
        items = []
        for m in models:
            eff = get_effective_rates(m)
            items.append({
                "id": m["id"],
                "provider": m.get("provider"),
                "type": m.get("type", "text"),
                "source_type": m.get("source_type", "direct"),
                "billing_unit": m.get("billing_unit"),
                "context_window": m.get("context_window"),
                "platform_fee": eff["platform_fee"],
                "currency": curr,
                "effective_input_per_1m": round(eff["input_per_1m"] * rate, 6) if eff["input_per_1m"] is not None else None,
                "effective_cached_input_per_1m": round(eff["cached_input_per_1m"] * rate, 6) if eff["cached_input_per_1m"] is not None else None,
                "effective_output_per_1m": round(eff["output_per_1m"] * rate, 6) if eff["output_per_1m"] is not None else None,
                "effective_unit_cost": round(eff["per_unit"] * rate, 6) if eff["per_unit"] is not None else None,
                "fixed_monthly_cost": round(eff["monthly"] * rate, 2) if eff["monthly"] is not None else None,
                "tags": m.get("tags", []),
                "description": m.get("description", ""),
            })
        _print_json({
            "metadata": meta,
            "currency": curr,
            "currency_updated": currency_date,
            "count": len(items),
            "models": items,
        })
        return

    if not models:
        console.print("[bold yellow]No models match the specified filters.[/bold yellow]")
        return

    table = Table(
        title=f"AI Models Pricing Database ({curr})",
        show_lines=True,
        caption=f"[dim]Pricing updated: {meta.get('last_updated', 'Unknown')} | Rates cached: {currency_date}[/dim]",
        caption_justify="right",
    )
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Provider", style="magenta")
    table.add_column("Type", justify="center")
    table.add_column("Source", justify="center", style="yellow")
    table.add_column("Input (1M)", justify="right", style="green")
    table.add_column("Output / Unit", justify="right", style="green")
    table.add_column("Capabilities", style="dim")

    for m in models:
        eff = get_effective_rates(m)
        m_type = m.get("type", "text")
        unit_lbl = format_unit_label(m.get("billing_unit"), m_type)
        tags = ", ".join(m.get("tags", []))
        fee_pct = eff["platform_fee"] * 100

        str_in = f"{eff['input_per_1m'] * rate:.4f}" if eff["input_per_1m"] is not None else "-"

        if eff["output_per_1m"] is not None:
            str_out = f"{eff['output_per_1m'] * rate:.4f} (/1M)"
        elif eff["per_unit"] is not None:
            str_out = f"{eff['per_unit'] * rate:.4f} (/{unit_lbl})"
        elif eff["monthly"] is not None:
            str_out = f"~{eff['monthly'] * rate:.0f} {curr}/mo"
        elif m_type == "gateway":
            str_out = "Custom"
        else:
            str_out = "-"

        source_label = m.get("source_type", "direct").capitalize()
        if fee_pct > 0:
            source_label += f" (+{fee_pct:.1f}%)"

        table.add_row(m["id"], m["provider"], m_type, source_label, str_in, str_out, tags)

    console.print(table)


@app.command()
def calc(
    model: str = typer.Argument(..., help="Model ID or alias (e.g., claude-opus-4.7, gpt-5.5, veo-3)"),
    input_tokens: int = typer.Option(0, "--input", "-i", help="Number of uncached input tokens"),
    output_tokens: int = typer.Option(0, "--output", "-o", help="Number of output tokens"),
    cached_input_tokens: int = typer.Option(0, "--cached-input", help="Number of cached input tokens (cache read)"),
    units: float = typer.Option(0.0, "--units", "-u", help="Number of units (images, seconds, minutes, songs, 1M chars, or months)"),
    batch: bool = typer.Option(False, "--batch", "-b", help="Apply Batch API discount (if supported by provider)"),
    currency: str = typer.Option("USD", "--currency", "-c", help="Target currency (e.g., USD, TRY, EUR)"),
    as_json: bool = typer.Option(False, "--json", help="Output structured JSON"),
) -> None:
    """Calculates the exact cost of an AI API operation with fee and discount breakdowns."""
    m = get_model_by_id(model)
    if not m:
        _handle_missing_model(model, as_json=as_json)

    m_type = m.get("type", "text")
    if m_type == "text" and not input_tokens and not output_tokens and not cached_input_tokens and not as_json:
        console.print("[bold yellow]Warning:[/bold yellow] No tokens provided. Use --input, --cached-input, and/or --output.")
    elif m_type not in ("text", "gateway") and not units and not as_json:
        unit_lbl = format_unit_label(m.get("billing_unit"), m_type)
        console.print(f"[bold yellow]Warning:[/bold yellow] No units provided. Use --units (billed per {unit_lbl}).")

    bd = calculate_cost_breakdown(
        model=m,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cached_input_tokens=cached_input_tokens,
        units=units,
        batch=batch,
    )
    rate, curr = get_exchange_rate(currency)
    meta = get_pricing_metadata()

    if as_json:
        _print_json({
            "model_id": bd["model_id"],
            "provider": bd["provider"],
            "source_type": bd["source_type"],
            "model_type": bd["model_type"],
            "billing_unit": bd["billing_unit"],
            "is_custom_pricing": bd["is_custom_pricing"],
            "usage_summary": bd["usage_summary"],
            "currency": curr,
            "raw_base_cost": round(bd["raw_base_usd"] * rate, 6),
            "batch_applied": bd["batch_applied"],
            "batch_discount_rate": bd["batch_discount_rate"],
            "batch_savings": round(bd["batch_savings_usd"] * rate, 6),
            "base_cost": round(bd["base_usd"] * rate, 6),
            "platform_fee_rate": bd["platform_fee_rate"],
            "platform_fee_cost": round(bd["platform_fee_usd"] * rate, 6),
            "total_cost": round(bd["total_usd"] * rate, 6),
            "last_updated": meta.get("last_updated", "Unknown"),
        })
        return

    lines = [
        f"Model: [cyan]{bd['model_id']}[/cyan]",
        f"Provider: [magenta]{bd['provider']}[/magenta]",
        f"Source: [yellow]{bd['source_type'].capitalize()}[/yellow]",
        f"Task: {bd['usage_summary']}",
    ]

    if batch and not bd["batch_applied"] and m_type == "text":
        lines.append("[dim]Note: Batch discount is not available for this model/source.[/dim]")

    if bd["is_custom_pricing"]:
        lines.append("\n[bold yellow]Total Cost: Custom Enterprise Pricing[/bold yellow]")
    else:
        if bd["batch_applied"] or bd["platform_fee_rate"] > 0:
            lines.append("")
            if bd["batch_applied"]:
                lines.append(f"Standard Cost: {bd['raw_base_usd'] * rate:.4f} {curr}")
                lines.append(
                    f"Batch Savings (-{bd['batch_discount_rate'] * 100:.0f}%): -{bd['batch_savings_usd'] * rate:.4f} {curr}"
                )
            lines.append(f"Base Cost: {bd['base_usd'] * rate:.4f} {curr}")
            if bd["platform_fee_rate"] > 0:
                lines.append(
                    f"Platform Fee ({bd['platform_fee_rate'] * 100:.1f}%): {bd['platform_fee_usd'] * rate:.4f} {curr}"
                )

        lines.append(f"\n[bold green]Total Cost: {bd['total_usd'] * rate:.4f} {curr}[/bold green]")

    panel = Panel(
        "\n".join(lines),
        title="Cost Calculation",
        subtitle=f"[dim]Based on {meta.get('last_updated', 'Unknown')} rates[/dim]",
        expand=False,
    )
    console.print(panel)


@app.command()
def estimate(
    model: str = typer.Argument(..., help="Model ID or alias"),
    requests_per_day: float = typer.Option(1000, "--requests-per-day", "-r", help="Average API requests per day"),
    input_tokens: int = typer.Option(2000, "--input", "-i", help="Average uncached input tokens per request"),
    output_tokens: int = typer.Option(500, "--output", "-o", help="Average output tokens per request"),
    cached_input_tokens: int = typer.Option(0, "--cached-input", help="Average cached input tokens per request"),
    units: float = typer.Option(1.0, "--units", "-u", help="Average units per request (for image/video/audio)"),
    days: int = typer.Option(30, "--days", "-d", help="Billing period in days (default: 30)"),
    batch: bool = typer.Option(False, "--batch", "-b", help="Apply Batch API discount if available"),
    currency: str = typer.Option("USD", "--currency", "-c", help="Target currency"),
    as_json: bool = typer.Option(False, "--json", help="Output structured JSON"),
) -> None:
    """Projects daily, monthly, and annual API budget for a recurring workload."""
    m = get_model_by_id(model)
    if not m:
        _handle_missing_model(model, as_json=as_json)

    est = estimate_monthly_cost(
        model=m,
        requests_per_day=requests_per_day,
        avg_input_tokens=input_tokens,
        avg_output_tokens=output_tokens,
        avg_cached_input_tokens=cached_input_tokens,
        avg_units=units,
        days=days,
        batch=batch,
    )
    rate, curr = get_exchange_rate(currency)
    meta = get_pricing_metadata()

    if as_json:
        _print_json({
            "model_id": est["model_id"],
            "provider": est["provider"],
            "source_type": est["source_type"],
            "model_type": est["model_type"],
            "currency": curr,
            "requests_per_day": est["requests_per_day"],
            "days": est["days"],
            "per_request_cost": round(est["per_request_usd"] * rate, 6),
            "daily_cost": round(est["daily_usd"] * rate, 4),
            "period_base_cost": round(est["period_base_usd"] * rate, 4),
            "period_fee_cost": round(est["period_fee_usd"] * rate, 4),
            "period_total_cost": round(est["period_total_usd"] * rate, 4),
            "annual_total_cost": round(est["annual_total_usd"] * rate, 2),
            "period_requests": est["period_requests"],
            "period_input_tokens": est["period_input_tokens"],
            "period_cached_input_tokens": est["period_cached_input_tokens"],
            "period_output_tokens": est["period_output_tokens"],
            "last_updated": meta.get("last_updated", "Unknown"),
        })
        return

    lines = [
        f"Model: [cyan]{est['model_id']}[/cyan] ([magenta]{est['provider']}[/magenta])",
        f"Traffic: {est['requests_per_day']:g} req/day ({est['period_requests']:,.0f} req / {est['days']}d)",
    ]
    if est["model_type"] == "text":
        lines.append(
            f"Monthly Volume: {est['period_input_tokens'] / 1_000_000:.2f}M in / "
            f"{est['period_output_tokens'] / 1_000_000:.2f}M out"
        )

    if est["is_custom_pricing"]:
        lines.append("\n[bold yellow]Projected Spend: Custom Enterprise Pricing[/bold yellow]")
    else:
        lines.append("")
        lines.append(f"Cost / Request: {est['per_request_usd'] * rate:.6f} {curr}")
        lines.append(f"Daily Spend:    {est['daily_usd'] * rate:.4f} {curr}")
        if est["period_fee_usd"] > 0:
            lines.append(f"{est['days']}-Day Base:    {est['period_base_usd'] * rate:.2f} {curr}")
            lines.append(f"{est['days']}-Day Fee:     {est['period_fee_usd'] * rate:.2f} {curr}")
        lines.append(f"[bold green]{est['days']}-Day Total:   {est['period_total_usd'] * rate:,.2f} {curr}[/bold green]")
        lines.append(f"Annual (365d):  {est['annual_total_usd'] * rate:,.2f} {curr}")

    console.print(
        Panel(
            "\n".join(lines),
            title="Workload Budget Estimate",
            subtitle=f"[dim]Based on {meta.get('last_updated', 'Unknown')} rates[/dim]",
            expand=False,
        )
    )


@app.command()
def recommend(
    task: str = typer.Argument(..., help="Describe your task (e.g., 'fast cheap coding', 'agentic vision')"),
    limit: int = typer.Option(3, "--limit", "-l", help="Number of recommendations"),
    model_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by model type (text, image, video, audio)"),
    max_cost: Optional[float] = typer.Option(None, "--max-cost", help="Max effective USD input/unit price"),
    include_legacy: bool = typer.Option(False, "--include-legacy", help="Include legacy models in recommendations"),
    currency: str = typer.Option("USD", "--currency", "-c", help="Target currency"),
    as_json: bool = typer.Option(False, "--json", help="Output structured JSON"),
) -> None:
    """Recommends the most cost-effective models for a given task."""
    models = recommend_models(
        task,
        limit=limit,
        model_type=model_type,
        max_input_cost=max_cost,
        include_legacy=include_legacy,
    )
    meta = get_pricing_metadata()
    rate, curr = get_exchange_rate(currency)

    if as_json:
        _print_json({
            "task": task,
            "currency": curr,
            "count": len(models),
            "recommendations": [
                {
                    "rank": idx,
                    "id": m["id"],
                    "provider": m.get("provider"),
                    "type": m.get("type", "text"),
                    "description": m.get("description", ""),
                    "tags": m.get("tags", []),
                    "effective_input_per_1m": (
                        round(get_effective_rates(m)["input_per_1m"] * rate, 6)
                        if get_effective_rates(m)["input_per_1m"] is not None
                        else None
                    ),
                    "effective_unit_cost": (
                        round(get_effective_rates(m)["per_unit"] * rate, 6)
                        if get_effective_rates(m)["per_unit"] is not None
                        else None
                    ),
                }
                for idx, m in enumerate(models, 1)
            ],
        })
        return

    if not models:
        console.print("[bold yellow]No models match this task clearly. Try other keywords or relax filters.[/bold yellow]")
        return

    last_updated = meta.get("last_updated", "Unknown")
    console.print(f"\n[bold cyan]Top {len(models)} Recommendations for:[/bold cyan] '{task}' [dim](Data: {last_updated})[/dim]\n")

    for i, m in enumerate(models, 1):
        eff = get_effective_rates(m)
        unit_lbl = format_unit_label(m.get("billing_unit"), m.get("type", "text"))

        if eff["input_per_1m"] is not None and eff["output_per_1m"] is not None:
            cost_str = (
                f"{eff['input_per_1m'] * rate:.4f} in / {eff['output_per_1m'] * rate:.4f} out {curr} per 1M tokens"
            )
        elif eff["per_unit"] is not None:
            cost_str = f"{eff['per_unit'] * rate:.4f} {curr} / {unit_lbl}"
        elif eff["monthly"] is not None:
            cost_str = f"~{eff['monthly'] * rate:.0f} {curr} / month"
        else:
            cost_str = "Custom"

        p = Panel.fit(
            f"{m['description']}\nTags: [magenta]{', '.join(m.get('tags', []))}[/magenta]\nCost ref: [bold green]{cost_str}[/bold green]",
            title=f"#{i} {m['id']} ({m['provider']})",
        )
        console.print(p)


@app.command()
def sync(
    as_json: bool = typer.Option(False, "--json", help="Output structured JSON"),
) -> None:
    """Manually triggers a pricing and exchange rate update from remote sources."""
    if not as_json:
        console.print("[yellow]Syncing latest pricing data and exchange rates...[/yellow]")

    data = fetch_remote_pricing()
    rates = refresh_rates()

    if as_json:
        _print_json({
            "pricing_synced": bool(data),
            "last_updated": data.get("last_updated") if data else None,
            "currencies_synced": len(rates) > 1,
            "currency_count": len(rates),
        })
        if not data:
            raise typer.Exit(1)
        return

    if data:
        last_updated = data.get("last_updated", "Unknown")
        console.print(
            f"[bold green]Success![/bold green] Pricing updated to [cyan]{last_updated}[/cyan] "
            f"({len(rates)} currencies cached)."
        )
    else:
        console.print("[bold red]Error:[/bold red] Could not fetch remote pricing. Check your internet connection.")
        raise typer.Exit(1)


@app.command()
def compare(
    models: List[str] = typer.Argument(..., help="Two or more model IDs to compare side-by-side"),
    currency: str = typer.Option("USD", "--currency", "-c", help="Target currency"),
    as_json: bool = typer.Option(False, "--json", help="Output structured JSON"),
) -> None:
    """Provides a side-by-side comparison between two or more models."""
    if len(models) < 2:
        if as_json:
            _print_json({"error": "Please provide at least two model IDs to compare."})
        else:
            console.print("[bold red]Error:[/bold red] Please provide at least two model IDs to compare.")
        raise typer.Exit(1)

    resolved: List[dict] = []
    for mid in models:
        found = get_model_by_id(mid)
        if not found:
            _handle_missing_model(mid, as_json=as_json)
        resolved.append(found)

    rate, curr = get_exchange_rate(currency)

    if as_json:
        _print_json({
            "currency": curr,
            "models": [
                {
                    "id": m["id"],
                    "provider": m.get("provider"),
                    "source_type": m.get("source_type", "direct"),
                    "platform_fee": m.get("platform_fee", 0.0),
                    "type": m.get("type", "text"),
                    "context_window": m.get("context_window"),
                    "effective_input_per_1m": (
                        round(get_effective_rates(m)["input_per_1m"] * rate, 6)
                        if get_effective_rates(m)["input_per_1m"] is not None
                        else None
                    ),
                    "effective_cached_input_per_1m": (
                        round(get_effective_rates(m)["cached_input_per_1m"] * rate, 6)
                        if get_effective_rates(m)["cached_input_per_1m"] is not None
                        else None
                    ),
                    "effective_output_per_1m": (
                        round(get_effective_rates(m)["output_per_1m"] * rate, 6)
                        if get_effective_rates(m)["output_per_1m"] is not None
                        else None
                    ),
                    "effective_unit_cost": (
                        round(get_effective_rates(m)["per_unit"] * rate, 6)
                        if get_effective_rates(m)["per_unit"] is not None
                        else None
                    ),
                    "fixed_monthly_cost": (
                        round(get_effective_rates(m)["monthly"] * rate, 2)
                        if get_effective_rates(m)["monthly"] is not None
                        else None
                    ),
                    "tags": m.get("tags", []),
                }
                for m in resolved
            ],
        })
        return

    styles = ["cyan", "magenta", "green", "yellow", "blue"]
    title = " vs ".join(m["id"] for m in resolved)
    table = Table(title=f"Comparison: {title}", show_lines=True)
    table.add_column("Attribute", style="bold white")
    for idx, m in enumerate(resolved):
        table.add_column(m["id"], style=styles[idx % len(styles)], justify="center")

    def fmt_in(m_data: dict) -> str:
        eff = get_effective_rates(m_data)
        if eff["input_per_1m"] is None:
            return "-"
        return f"{eff['input_per_1m'] * rate:.4f} {curr} (/1M)"

    def fmt_cached(m_data: dict) -> str:
        eff = get_effective_rates(m_data)
        if eff["cached_input_per_1m"] is None:
            return "-"
        return f"{eff['cached_input_per_1m'] * rate:.4f} {curr} (/1M)"

    def fmt_out(m_data: dict) -> str:
        eff = get_effective_rates(m_data)
        unit_lbl = format_unit_label(m_data.get("billing_unit"), m_data.get("type", "text"))
        if eff["output_per_1m"] is not None:
            return f"{eff['output_per_1m'] * rate:.4f} {curr} (/1M)"
        if eff["per_unit"] is not None:
            return f"{eff['per_unit'] * rate:.4f} {curr} (/{unit_lbl})"
        if eff["monthly"] is not None:
            return f"~{eff['monthly'] * rate:.0f} {curr}/mo"
        if m_data.get("type") == "gateway":
            return "Custom"
        return "-"

    table.add_row("Provider", *[m["provider"] for m in resolved])
    table.add_row("Source", *[m.get("source_type", "direct").capitalize() for m in resolved])
    table.add_row("Platform Fee", *[f"{m.get('platform_fee', 0.0) * 100:.1f}%" for m in resolved])
    table.add_row("Type", *[m.get("type", "text") for m in resolved])
    table.add_row("Context Window", *[_format_context_window(m.get("context_window")) for m in resolved])
    table.add_row("Input Cost", *[fmt_in(m) for m in resolved])
    table.add_row("Cached Input", *[fmt_cached(m) for m in resolved])
    table.add_row("Output / Unit Cost", *[fmt_out(m) for m in resolved])
    table.add_row("Tags", *[", ".join(m.get("tags", [])) for m in resolved])

    console.print(table)


@app.command()
def report_price(
    model_id: str = typer.Argument(..., help="Model ID that has a price change"),
    new_input: Optional[float] = typer.Option(None, "--input", help="New input price per 1M tokens"),
    new_output: Optional[float] = typer.Option(None, "--output", help="New output price per 1M tokens"),
    source: Optional[str] = typer.Option(None, "--source", "-s", help="Source URL for the new pricing"),
) -> None:
    """Generates a GitHub Issue link to report a pricing update."""
    title = f"Price Update: {model_id}"
    body = (
        f"Model ID: {model_id}\n"
        f"Proposed Input: {new_input}\n"
        f"Proposed Output: {new_output}\n"
        f"Source: {source}\n\n"
        "Reported via AI-Cost-CLI."
    )

    base_url = "https://github.com/ufhouck/aicost/issues/new"
    params = {
        "title": title,
        "body": body,
        "labels": "pricing-update",
    }
    url = f"{base_url}?{urllib.parse.urlencode(params)}"

    console.print("\n[bold cyan]Opening GitHub to report this change...[/bold cyan]")
    console.print(f"[dim]{url}[/dim]\n")
    webbrowser.open(url)


@app.command()
def mcp() -> None:
    """Starts the Model Context Protocol (MCP) standard IO server."""
    from aicost.mcp_server import start_server

    start_server()


if __name__ == "__main__":
    app()
