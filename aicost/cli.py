import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from aicost.calculator import get_pricing_data, get_model_by_id, calculate_text_cost, calculate_image_cost
from aicost.currency import convert_cost
from aicost.recommender import recommend_models

app = typer.Typer(help="AI-Cost-CLI: Calculate, Compare, and Recommend AI API Costs.")
console = Console()

@app.command()
def list(currency: str = typer.Option("USD", "--currency", "-c", help="Target currency (e.g., USD, TRY, EUR)")):
    """Lists all available AI models and their pricing."""
    models = get_pricing_data()
    
    table = Table(title=f"AI Models Pricing Database ({currency.upper()})", show_lines=True)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Provider", style="magenta")
    table.add_column("Type", justify="center")
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
        str_out = f"{c_out:.4f} (1M)" if c_out is not None else f"{c_unit:.4f} (Unit)"
        
        table.add_row(m["id"], m["provider"], m_type, str_in, str_out, tags)
        
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

    panel = Panel(
        f"Model: [cyan]{m['id']}[/cyan]\nProvider: [magenta]{m['provider']}[/magenta]\nTask: {desc}\n\n[bold green]Total Cost: {final_cost:.4f} {currency_fmt}[/bold green]",
        title="Cost Calculation",
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
    if not models:
        console.print("[bold yellow]No models match this task clearly. Try other keywords.[/bold yellow]")
        return
        
    console.print(f"\n[bold cyan]Top {len(models)} Recommendations for:[/bold cyan] '{task}'\n")
    
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
def mcp():
    """Starts the Model Context Protocol (MCP) standard IO server."""
    from aicost.mcp_server import start_server
    start_server()

if __name__ == "__main__":
    app()
