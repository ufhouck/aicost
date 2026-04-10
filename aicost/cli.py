import warnings
# Suppress the urllib3 NotOpenSSLWarning on macOS/LibreSSL systems
warnings.filterwarnings("ignore", message=".*urllib3 v2 only supports OpenSSL 1.1.1+.*")

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from aicost.calculator import (
    get_pricing_data, 
    get_model_by_id, 
    calculate_text_cost, 
    calculate_image_cost, 
    get_pricing_metadata,
    fetch_remote_pricing
)
from aicost.currency import convert_cost, get_currency_date
from aicost.recommender import recommend_models
import webbrowser
import urllib.parse

app = typer.Typer(help="AI-Cost-CLI: Calculate, Compare, and Recommend AI API Costs.")
console = Console()

@app.command()
def list(currency: str = typer.Option("USD", "--currency", "-c", help="Target currency (e.g., USD, TRY, EUR)")):
    """Lists all available AI models and their pricing."""
    models = get_pricing_data()
    meta = get_pricing_metadata()
    last_updated = meta.get("last_updated", "Unknown")
    currency_date = get_currency_date()
    
    table = Table(
        title=f"AI Models Pricing Database ({currency.upper()})", 
        show_lines=True,
        caption=f"[dim]Pricing details updated: {last_updated} | Currency matched: {currency_date}[/dim]",
        caption_justify="right"
    )
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Provider", style="magenta")
    table.add_column("Type", justify="center")
    table.add_column("Source", justify="center", style="yellow")
    table.add_column("Input Cost (1M)", justify="right", style="green")
    table.add_column("Output/Unit Cost", justify="right", style="green")
    table.add_column("Capabilities", style="dim")
    
    for m in models:
        c_in = m.get("cost_per_1m_input_tokens")
        c_out = m.get("cost_per_1m_output_tokens")
        c_unit = m.get("cost_per_unit")
        m_type = m.get("type", "text")
        tags = ", ".join(m.get("tags", []))
        
        if c_in is not None: c_in = convert_cost(c_in, currency)
        if c_out is not None: c_out = convert_cost(c_out, currency)
        if c_unit is not None: c_unit = convert_cost(c_unit, currency)
        
        str_in = f"{c_in:.4f}" if c_in is not None else "-"
        
        if c_out is not None:
            str_out = f"{c_out:.4f} (1M)"
        elif c_unit is not None:
            str_out = f"{c_unit:.4f} (Unit)"
        else:
            str_out = "-"
        
        # Display gateway monthly cost if available
        if m.get("source_type") == "gateway" and m.get("fixed_monthly_cost"):
            str_out = f"~{convert_cost(m['fixed_monthly_cost'], currency):.0f} {currency.upper()}/mo"
            
        source_label = m.get("source_type", "direct").capitalize()
        table.add_row(m["id"], m["provider"], m_type, source_label, str_in, str_out, tags)
        
    console.print(table)

@app.command()
def calc(
    model: str = typer.Argument(..., help="Model ID (e.g., gpt-4o, flux-1-pro)"),
    input_tokens: int = typer.Option(0, "--input", "-i", help="Number of input tokens"),
    output_tokens: int = typer.Option(0, "--output", "-o", help="Number of output tokens"),
    units: int = typer.Option(0, "--units", "-u", help="Number of units (for image/video)"),
    currency: str = typer.Option("USD", "--currency", "-c", help="Target currency")
):
    """Calculates the cost of an AI operation."""
    m = get_model_by_id(model)
    if not m:
        console.print(f"[bold red]Error:[/bold red] Model '{model}' not found in database.")
        raise typer.Exit(1)
        
    if m.get("type") == "text":
        if not input_tokens and not output_tokens:
            console.print("[bold yellow]Warning:[/bold yellow] No tokens provided. Use --input and --output.")
        usd_cost = calculate_text_cost(m, input_tokens, output_tokens)
        desc = f"Text: {input_tokens} in / {output_tokens} out"
    else:
        if not units:
            console.print("[bold yellow]Warning:[/bold yellow] No units provided. Use --units.")
        usd_cost = calculate_image_cost(m, units)
        desc = f"Image/Video: {units} units"

    final_cost = convert_cost(usd_cost, currency)
    currency_fmt = currency.upper()
    meta = get_pricing_metadata()

    # Breakdown for fees
    breakdown = f"Model: [cyan]{m['id']}[/cyan]\nProvider: [magenta]{m['provider']}[/magenta]\nSource: [yellow]{m.get('source_type', 'direct').capitalize()}[/yellow]\nTask: {desc}\n"
    
    fee = m.get("platform_fee", 0.0)
    if fee > 0:
        base_cost = final_cost / (1 + fee)
        fee_amount = final_cost - base_cost
        breakdown += f"\nBase Cost: {base_cost:.4f} {currency_fmt}\nPlatform Fee ({fee*100:.1f}%): {fee_amount:.4f} {currency_fmt}"

    panel = Panel(
        f"{breakdown}\n\n[bold green]Total Cost: {final_cost:.4f} {currency_fmt}[/bold green]",
        title="Cost Calculation",
        subtitle=f"[dim]Based on {meta.get('last_updated', 'Unknown')} rates[/dim]",
        expand=False
    )
    console.print(panel)

@app.command()
def recommend(
    task: str = typer.Argument(..., help="Describe your task (e.g., 'fast cheap ocr', 'coding reasoning')"),
    limit: int = typer.Option(3, "--limit", "-l", help="Number of recommendations"),
    currency: str = typer.Option("USD", "--currency", "-c", help="Target currency")
):
    """Recommends the best models for a given task."""
    models = recommend_models(task, limit=limit)
    meta = get_pricing_metadata()
    if not models:
        console.print("[bold yellow]No models match this task clearly. Try other keywords.[/bold yellow]")
        return
        
    last_updated = meta.get("last_updated", "Unknown")
    console.print(f"\n[bold cyan]Top {len(models)} Recommendations for:[/bold cyan] '{task}' [dim](Data: {last_updated})[/dim]\n")
    
    for i, m in enumerate(models, 1):
        c_in = m.get("cost_per_1m_input_tokens")
        
        cost_str = ""
        if c_in is not None:
             cost_str = f"{convert_cost(c_in, currency):.4f} {currency.upper()} / 1M Input"
        else:
             cost_str = f"{convert_cost(m.get('cost_per_unit', 0), currency):.4f} {currency.upper()} / Unit"
             
        p = Panel.fit(
            f"{m['description']}\nTags: [magenta]{', '.join(m.get('tags', []))}[/magenta]\nCost ref: [bold green]{cost_str}[/bold green]",
            title=f"#{i} {m['id']} ({m['provider']})"
        )
        console.print(p)

@app.command()
def sync():
    """Manually triggers a pricing update from the remote GitHub repository."""
    console.print("[yellow]Syncing latest pricing data from GitHub...[/yellow]")
    data = fetch_remote_pricing()
    if data:
        last_updated = data.get("last_updated", "Unknown")
        console.print(f"[bold green]Success![/bold green] Pricing updated to: [cyan]{last_updated}[/cyan]")
    else:
        console.print("[bold red]Error:[/bold red] Could not fetch remote pricing. Check your internet connection.")

@app.command()
def compare(
    model1: str = typer.Argument(..., help="First model ID"),
    model2: str = typer.Argument(..., help="Second model ID"),
    currency: str = typer.Option("USD", "--currency", "-c", help="Target currency")
):
    """Provides a side-by-side comparison between two models."""
    m1 = get_model_by_id(model1)
    m2 = get_model_by_id(model2)
    
    if not m1 or not m2:
        missing = model1 if not m1 else model2
        console.print(f"[bold red]Error:[/bold red] Model '{missing}' not found.")
        return

    table = Table(title=f"Comparison: {model1} vs {model2}", show_lines=True)
    table.add_column("Attribute", style="bold white")
    table.add_column(m1['id'], style="cyan", justify="center")
    table.add_column(m2['id'], style="magenta", justify="center")

    def fmt_price(m_data, input_val=True):
        # Handle Gateway fixed monthly costs
        if m_data.get("source_type") == "gateway" and m_data.get("fixed_monthly_cost"):
            val = convert_cost(m_data["fixed_monthly_cost"], currency)
            return f"~{val:.0f} {currency.upper()}/mo"
            
        fee = m_data.get("platform_fee", 0.0)
        base_val = m_data.get('cost_per_1m_input_tokens') if input_val else (m_data.get('cost_per_1m_output_tokens') or m_data.get('cost_per_unit'))
        if base_val is None: return "-"
        
        # Calculate effective cost (base + platform fee)
        effective_val = convert_cost(base_val * (1 + fee), currency)
        suffix = " (1M)" if m_data.get("type") == "text" else " (Unit)"
        return f"{effective_val:.4f} {currency.upper()}{suffix}"

    table.add_row("Provider", m1['provider'], m2['provider'])
    table.add_row("Source", m1.get('source_type', 'direct').capitalize(), m2.get('source_type', 'direct').capitalize())
    table.add_row("Platform Fee", f"{m1.get('platform_fee', 0.0)*100:.1f}%", f"{m2.get('platform_fee', 0.0)*100:.1f}%")
    table.add_row("Type", m1.get('type'), m2.get('type'))
    table.add_row("Input Cost", fmt_price(m1, True), fmt_price(m2, True))
    table.add_row("Output/Unit Cost", fmt_price(m1, False), fmt_price(m2, False))
    table.add_row("Tags", ", ".join(m1.get('tags', [])), ", ".join(m2.get('tags', [])))

    console.print(table)

@app.command()
def report_price(
    model_id: str = typer.Argument(..., help="Model ID that has a price change"),
    new_input: float = typer.Option(None, "--input", help="New input price per 1M tokens"),
    new_output: float = typer.Option(None, "--output", help="New output price per 1M tokens"),
    source: str = typer.Option(None, "--source", "-s", help="Source URL for the new pricing")
):
    """Generates a GitHub Issue link to report a pricing update."""
    title = f"Price Update: {model_id}"
    body = f"Model ID: {model_id}\nProposed Input: {new_input}\nProposed Output: {new_output}\nSource: {source}\n\nReported via AI-Cost-CLI."
    
    base_url = "https://github.com/ufhouck/aicost/issues/new"
    params = {
        "title": title,
        "body": body,
        "labels": "pricing-update"
    }
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    
    console.print(f"\n[bold cyan]Opening GitHub to report this change...[/bold cyan]")
    console.print(f"[dim]{url}[/dim]\n")
    webbrowser.open(url)

@app.command()
def mcp():
    """Starts the Model Context Protocol (MCP) standard IO server."""
    from aicost.mcp_server import start_server
    start_server()

if __name__ == "__main__":
    app()
