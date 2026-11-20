# Contributing to AI-Cost-CLI

Thank you for your interest in contributing! This guide will help you get started.

## Ways to Contribute

### 🏷️ Pricing Updates

The most common contribution is updating model pricing. If you notice a price change:

**Option A — Use the CLI:**
```bash
aicost report-price gpt-5.5 --input 5.0 --output 30.0 --source "https://openai.com/api/pricing/"
```
This will open a pre-filled GitHub issue for review.

**Option B — Edit directly:**
1. Edit `data/pricing.json` (single source of truth for both Python `aicost-cli` and npm `aicost-mcp`)
2. Follow the existing v2.0 model entry format
3. Run tests to validate schema integrity: `pytest`
4. Submit a Pull Request with a link to the official pricing source

### 🐛 Bug Reports & ✨ Feature Requests

1. Check [existing issues](https://github.com/ufhouck/aicost/issues) first
2. Open an issue using the **Bug Report** or **Feature Request** template

## Development Setup

### Python CLI & Python MCP Server
```bash
git clone https://github.com/ufhouck/aicost.git
cd aicost
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
pytest
```

### Node.js / TypeScript MCP Server (`aicost-mcp`)
```bash
cd npm
npm install
npm run build
node dist/index.js --version
```

## Project Structure

```text
AI-Cost-CLI/
├── aicost/                 # Python CLI & Python MCP server
│   ├── cli.py              # CLI commands (Typer + Rich)
│   ├── calculator.py       # Cost, caching, batch & monthly budget math
│   ├── currency.py         # 200+ currency conversion with multi-CDN fallback
│   ├── recommender.py      # Task-based model recommendation engine
│   └── mcp_server.py       # Python MCP server implementation
├── npm/                    # TypeScript npm MCP package (aicost-mcp)
│   ├── src/                # MCP server source (McpServer + Zod)
│   └── package.json        # npm manifest
├── data/
│   └── pricing.json        # Canonical model pricing database (v2.0)
├── scripts/
│   └── automate_pricing.py # Weekly automated pricing sync
├── tests/
│   └── test_aicost.py      # Schema, calculation, CLI & MCP unit tests
└── server.json             # Official MCP Registry manifest (npm + PyPI)
```

## Pricing Data Format (`schema_version: "2.0"`)

```json
{
  "id": "model-id",
  "aliases": ["short-alias"],
  "openrouter_id": "provider/model-id",
  "provider": "Provider Name",
  "source_type": "direct|aggregator|gateway",
  "type": "text|image|video|audio|gateway",
  "billing_unit": "1m_tokens|image|second|minute|song|clip|1m_chars|month|custom",
  "context_window": 200000,
  "cost_per_1m_input_tokens": 5.0,
  "cost_per_1m_cached_input_tokens": 0.5,
  "cost_per_1m_output_tokens": 25.0,
  "batch_discount": 0.5,
  "tags": ["coding", "reasoning", "agentic"],
  "description": "Short description of the model."
}
```

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
