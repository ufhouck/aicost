# AI-Cost-CLI & MCP (`aicost-mcp`)

[![PyPI](https://img.shields.io/pypi/v/aicost-cli.svg)](https://pypi.org/project/aicost-cli/)
[![npm](https://img.shields.io/npm/v/aicost-mcp.svg)](https://www.npmjs.com/package/aicost-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![MCP Registry](https://img.shields.io/badge/MCP-Registry-green.svg)](https://registry.modelcontextprotocol.io)

A terminal-based AI API cost calculator, monthly workload budget estimator, recommender, and **Model Context Protocol (MCP)** server. Compare Direct providers vs. Aggregators/Gateways, factor in prompt caching and Batch API discounts, and convert across **200+ currencies**.

<!-- mcp-name: io.github.ufhouck/aicost-cli -->

## Preview: Direct vs. Aggregator Comparison

Compare the effective cost of using models directly vs. through gateways like **OpenRouter**, including platform fees, context windows, and prompt-caching rates.

```text
                Comparison: gpt-4o vs openrouter/gpt-4o                 
┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Attribute          ┃         gpt-4o          ┃   openrouter/gpt-4o   ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━┩
│ Provider           │         OpenAI          │      OpenRouter       │
├────────────────────┼─────────────────────────┼───────────────────────┤
│ Source             │         Direct          │      Aggregator       │
├────────────────────┼─────────────────────────┼───────────────────────┤
│ Platform Fee       │          0.0%           │         5.5%          │
├────────────────────┼─────────────────────────┼───────────────────────┤
│ Context Window     │          128K           │         128K          │
├────────────────────┼─────────────────────────┼───────────────────────┤
│ Input Cost         │    2.5000 USD (/1M)     │   2.6375 USD (/1M)    │
├────────────────────┼─────────────────────────┼───────────────────────┤
│ Cached Input       │    1.2500 USD (/1M)     │   1.3188 USD (/1M)    │
├────────────────────┼─────────────────────────┼───────────────────────┤
│ Output / Unit Cost │    10.0000 USD (/1M)    │   10.5500 USD (/1M)   │
└────────────────────┴─────────────────────────┴───────────────────────┘
```

## Supported Models

### Text Models
| Model | Provider | Input/1M | Cached/1M | Output/1M | Context |
|-------|----------|----------|-----------|-----------|---------|
| Claude Opus 4.7 | Anthropic | $5.00 | $0.50 | $25.00 | 200K |
| GPT-5.5 | OpenAI | $5.00 | $1.25 | $30.00 | 12M |
| GPT-5.5 Pro | OpenAI | $30.00 | $15.00 | $180.00 | 12M |
| Claude Sonnet 4.6 | Anthropic | $3.00 | $0.30 | $15.00 | 200K |
| Gemini 3.1 Pro | Google | $2.00 | $0.50 | $12.00 | 2M |
| DeepSeek R1 | DeepSeek | $0.55 | $0.14 | $2.19 | 128K |
| Gemini 3.1 Flash-Lite | Google | $0.25 | $0.0625 | $1.50 | 1M |
| DeepSeek V3 | DeepSeek | $0.14 | $0.014 | $0.28 | 128K |

### Image, Video & Audio Models
| Model | Provider | Price | Billing Unit | Type |
|-------|----------|-------|--------------|------|
| Imagen 4 Fast | Google | $0.02 | per image | Image |
| GPT-Image-1 | OpenAI | $0.02 | per image | Image |
| DALL-E 3 | OpenAI | $0.04 | per image | Image |
| Imagen 4 Ultra | Google | $0.06 | per image | Image |
| Veo 3 Lite | Google | $0.05 | per second | Video |
| Veo 3 | Google | $0.40 | per second | Video |
| Lyria 3 Clip | Google | $0.04 | per clip | Music |
| Lyria 3 Pro | Google | $0.08 | per song | Music |
| Whisper | OpenAI | $0.006 | per minute | Speech-to-Text |
| TTS Standard / HD | OpenAI | $15 / $30 | per 1M chars | Text-to-Speech |

> Full catalog available via `aicost list --currency USD`

## Features

- **Direct vs. Aggregator & Gateway Math:** Automatically breaks down base API costs vs. middle-layer fees (e.g., OpenRouter 5.5%) and enterprise gateway monthly tiers.
- **Prompt Caching & Batch Discounts:** First-class support for `--cached-input` read rates and `--batch` API discounts.
- **Monthly Workload Estimator (`aicost estimate`):** Forecast daily, 30-day, and annual API spend from expected request traffic.
- **200+ Currencies with Offline Resilience:** Powered by a 3-tier CDN currency engine (`TRY`, `EUR`, `GBP`, `AZN`, `AED`, `JPY`, etc.) with 24-hour local cache.
- **Scriptable `--json` Mode:** Every CLI command supports clean JSON output for CI/CD pipelines and AI agent skills.
- **Dual MCP Server Ecosystem (`npx` & `uvx`):** Zero-install MCP integration via npm (`aicost-mcp`) or PyPI (`aicost-cli`).

## Installation

### Python CLI (`pip` / `uv`)
```bash
pip install aicost-cli
```

### MCP Server (`npx` — Recommended for Claude Desktop, Cursor, Windsurf, VS Code)
Add to your MCP configuration (`claude_desktop_config.json` or `.cursor/mcp.json`):
```json
{
  "mcpServers": {
    "aicost": {
      "command": "npx",
      "args": ["-y", "aicost-mcp"]
    }
  }
}
```

Or run via Python `uvx`:
```json
{
  "mcpServers": {
    "aicost": {
      "command": "uvx",
      "args": ["--from", "aicost-cli", "aicost-mcp"]
    }
  }
}
```

## CLI Usage

### List & Filter Models
```bash
aicost list --currency TRY
aicost list --provider Google --type video --hide-legacy
aicost list --tag agentic --sort input --json
```

### Calculate Cost (with Caching & Batch Support)
```bash
# Standard text model calculation
aicost calc claude-opus-4.7 --input 200000 --cached-input 800000 --output 100000 --currency USD

# Batch API (-50%) calculation
aicost calc gpt-5.5 --input 1000000 --output 500000 --batch

# Aggregator fee breakdown
aicost calc openrouter/gpt-4o --input 1000000 --output 500000 --currency TRY

# Multimodal unit calculation (seconds, minutes, images)
aicost calc veo-3 --units 8 --currency USD
```

### Project Monthly Workload Budget
```bash
aicost estimate claude-sonnet-4.6 --requests-per-day 2500 --input 1800 --output 450 --currency USD
```

### Compare 2+ Models Side-by-Side
```bash
aicost compare claude-opus-4.7 gpt-5.5 gemini-3.1-pro --currency USD
```

### Get Task Recommendations
```bash
aicost recommend "fast cheap agentic coding" --max-cost 1.0 --currency USD
```

### Sync Latest Pricing & Exchange Rates
```bash
aicost sync
```

## Registries
- [PyPI — `aicost-cli`](https://pypi.org/project/aicost-cli/)
- [npm — `aicost-mcp`](https://www.npmjs.com/package/aicost-mcp)
- [MCP Registry](https://registry.modelcontextprotocol.io) — `io.github.ufhouck/aicost-cli`
- [Smithery.ai](https://smithery.ai/skills/ufhouck-oskt/aicost)
- [Skills.sh](https://skills.sh/ufhouck/aicost/aicost)

## Community & Governance

- [Contributing Guide](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security Policy](SECURITY.md)
- [Privacy Policy](PRIVACY.md)
- [Changelog](CHANGELOG.md)

## License

MIT — see [LICENSE](LICENSE) for details. Developed by [Ufuk Aydın](https://ufukaydin.com).
