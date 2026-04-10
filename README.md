# AI-Cost-CLI

A terminal-based calculator and recommendation engine for AI API costs. Supports multiple providers, local currency conversion, and automated pricing updates.

## Features

- **Direct Cost Calculation:** Calculate costs for text (tokens) and image (units) models.
- **Comparison Engine:** Side-by-side comparison of different models and providers.
- **Recommendation Engine:** Suggests models based on task keywords (e.g., `ocr`, `coding`, `cheap`).
- **Currency Conversion:** Real-time conversion to local currencies (TRY, EUR, etc.) with a 24-hour offline cache.
- **Automated Pricing:** Weekly automated updates from official documentation sources via GitHub Actions.
- **MCP Integration:** Functions as a [Model Context Protocol](https://modelcontextprotocol.io/) server for integration with AI agents (Cursor, Claude Desktop, etc.).

## Installation

```bash
git clone https://github.com/ufhouck/aicost.git
cd aicost
pip install -e .
```

## Usage

### Pricing & Sync
```bash
# List all models in USD
aicost list

# Sync latest verified prices from GitHub
aicost sync

# List in local currency
aicost list --currency TRY
```

### Cost Calculation
```bash
# Calculate token-based cost
aicost calc gpt-4o --input 1000000 --output 500000

# Compare two models side-by-side
aicost compare gpt-4o claude-3-5-sonnet --currency TRY
```

### Recommendations & Feedback
```bash
# Get recommendations for a specific task
aicost recommend "fast cheap ocr extraction"

# Report a price change (opens a pre-filled GitHub Issue)
aicost report-price gpt-4o --input 2.5 --output 10.0
```

### MCP Server
```bash
aicost mcp
```

## Registries
- [Smithery.ai](https://smithery.ai/skills/ufhouck-oskt/aicost)
- [Skills.sh](https://skills.sh/ufhouck/aicost/aicost)

## Contributing
The pricing database is located in `data/pricing.json`. Updates are automatically checked weekly, but manual Pull Requests are welcome for new models.

## License
MIT. Developed by [Ufuk Aydın](https://ufukaydin.com).
