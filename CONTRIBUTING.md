# Contributing to AI-Cost-CLI

Thank you for your interest in contributing! This guide will help you get started.

## Ways to Contribute

### 🏷️ Pricing Updates

The most common contribution is updating model pricing. If you notice a price change:

**Option A — Use the CLI:**
```bash
aicost report-price gpt-4o --input 2.5 --output 10.0 --source "https://openai.com/api/pricing/"
```
This will open a pre-filled GitHub issue for review.

**Option B — Edit directly:**
1. Edit `data/pricing.json`
2. Follow the existing model entry format
3. Submit a Pull Request with a link to the official pricing source

### 🐛 Bug Reports

1. Check [existing issues](https://github.com/ufhouck/aicost/issues) first
2. Use the **Bug Report** issue template
3. Include your Python version, OS, and steps to reproduce

### ✨ Feature Requests

1. Open an issue using the **Feature Request** template
2. Describe the use case and expected behavior
3. Discuss before implementing large changes

### 🔧 Code Contributions

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Test locally:
   ```bash
   pip install -e .
   aicost list --currency USD
   ```
5. Submit a Pull Request

## Development Setup

```bash
git clone https://github.com/ufhouck/aicost.git
cd aicost
python3 -m venv venv
source venv/bin/activate
pip install -e ".[mcp]"
```

## Project Structure

```
AI-Cost-CLI/
├── aicost/
│   ├── cli.py          # CLI commands (Typer)
│   ├── calculator.py   # Cost calculation & data loading
│   ├── currency.py     # Currency conversion
│   ├── recommender.py  # Model recommendation engine
│   └── mcp_server.py   # MCP server implementation
├── data/
│   └── pricing.json    # Model pricing database
├── scripts/
│   └── automate_pricing.py  # Automated pricing updates
└── server.json         # MCP server configuration
```

## Pricing Data Format

Each model entry in `data/pricing.json` follows this schema:

```json
{
  "id": "model-id",
  "provider": "Provider Name",
  "source_type": "direct|aggregator|gateway",
  "type": "text|image|gateway",
  "cost_per_1m_input_tokens": 0.0,
  "cost_per_1m_output_tokens": 0.0,
  "tags": ["tag1", "tag2"],
  "description": "Short description of the model."
}
```

**Important:** Always include the official source URL in your PR description when updating prices.

## Code Style

- Follow PEP 8
- Keep functions focused and well-documented
- Use type hints where practical

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
