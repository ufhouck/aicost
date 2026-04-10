import time
from rich.console import Console
from aicost.cli import console as cli_console
import aicost.cli as cli

# Override console to record output
cli_console.record = True
cli_console.width = 100

cli_console.print("[bold green]$[/bold green] aicost list --currency EUR")
time.sleep(0.5)
try:
    cli.list(currency="EUR")
except Exception as e:
    print(e)
    
cli_console.print("\n[bold green]$[/bold green] aicost recommend \"fast premium ocr\"")
time.sleep(0.5)
try:
    cli.recommend(task="fast premium ocr", limit=3, currency="USD")
except Exception as e:
    print(e)
    
cli_console.save_svg("demo.svg", title="AI-Cost-CLI 🚀")
print("Saved demo.svg")
