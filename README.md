# AI-Cost-CLI

A terminal-based calculator and recommendation engine for AI API costs. Supports multiple providers, local currency conversion, and automated pricing updates.

## Preview: Direct vs. Aggregator Comparison

Compare the effective cost of using models directly vs. through gateways like **OpenRouter**, including platform fees.

```text
                    Comparison: gpt-4o vs openrouter/gpt-4o                     
┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Attribute        ┃             gpt-4o              ┃    openrouter/gpt-4o    ┃
┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Provider         │             OpenAI              │       OpenRouter        │
├──────────────────┼─────────────────────────────────┼─────────────────────────┤
│ Source           │             Direct              │       Aggregator        │
├──────────────────┼─────────────────────────────────┼─────────────────────────┤
│ Platform Fee     │              0.0%               │          5.5%           │
├──────────────────┼─────────────────────────────────┼─────────────────────────┤
│ Type             │              text               │          text           │
├──────────────────┼─────────────────────────────────┼─────────────────────────┤
│ Input Cost       │        111.4775 TRY (1M)        │    117.6088 TRY (1M)    │
├──────────────────┼─────────────────────────────────┼─────────────────────────┤
│ Output/Unit Cost │        445.9100 TRY (1M)        │    470.4350 TRY (1M)    │
└──────────────────┴─────────────────────────────────┴─────────────────────────┘
```

## Features

- **Infrastructure Comparison:** Compare **Direct** providers vs. **Aggregators** (OpenRouter) and **Gateways** (Portkey, LiteLLM, Martian).
- **Transparent Commissions:** Automatically calculates platform fees (e.g., OpenRouter's 5.5% credit fee).
- **Direct Cost Calculation:** Full breakdown of base costs and platform middle-layer fees.
- **Currency Conversion:** Real-time conversion to local currencies (TRY, EUR, etc.) with offline fallback.
- **Automated Pricing:** Weekly automated updates from official provider documentation.
- **MCP Server:** Native support for AI agents (Cursor, Claude Desktop).

## Usage

### Infrastructure & Sync
```bash
# List all models including Source Type (Direct/Aggregator/Gateway)
aicost list --currency TRY

# Compare Direct vs. Aggregator pricing
aicost compare gpt-4o openrouter/gpt-4o --currency TRY
```

### Advanced Cost Calculation
Includes platform fee breakdowns for aggregators:
```bash
aicost calc openrouter/gpt-4o --input 1000000 --output 500000 --currency TRY
```

**Output Example:**
```text
╭───────── Cost Calculation ──────────╮
│ Model: openrouter/gpt-4o            │
│ Source: Aggregator                  │
│                                     │
│ Base Cost: 316.9976 TRY             │
│ Platform Fee (5.5%): 17.4349 TRY    │
│                                     │
│ Total Cost: 334.4325 TRY            │
╰─────────────────────────────────────╯
```

## Installation

```bash
git clone https://github.com/ufhouck/aicost.git
cd aicost
pip install -e .
```

## MCP Server
```bash
aicost mcp
```

## Registries
- [Smithery.ai](https://smithery.ai/skills/ufhouck-oskt/aicost)
- [Skills.sh](https://skills.sh/ufhouck/aicost/aicost)

## Contributing
The pricing database is located in `data/pricing.json`. Updates are automatically checked weekly.

## License
MIT. Developed by [Ufuk Aydın](https://ufukaydin.com).
