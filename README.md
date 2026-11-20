# AI-Cost-CLI & MCP (`aicost-mcp`)

[![PyPI](https://img.shields.io/pypi/v/aicost-cli.svg)](https://pypi.org/project/aicost-cli/)
[![npm](https://img.shields.io/npm/v/aicost-mcp.svg)](https://www.npmjs.com/package/aicost-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![MCP Registry](https://img.shields.io/badge/MCP-Registry-green.svg)](https://registry.modelcontextprotocol.io)

A terminal-based AI API cost calculator, monthly workload budget estimator, recommender, and **Model Context Protocol (MCP)** server. Covers **60+ curated multimodal models** plus **470+ live models** dynamically, compares Direct providers vs. Aggregators/Gateways, factors in prompt caching and Batch API discounts, and converts across **200+ currencies**.

<!-- mcp-name: io.github.ufhouck/aicost-cli -->

## Preview: Direct vs. Aggregator Comparison

Compare the effective cost of using frontier models directly vs. through gateways like **OpenRouter**, including platform fees, context windows, and prompt-caching rates.

```text
          Comparison: claude-sonnet-5.5 vs openrouter/claude-sonnet-5.5          
┏━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Attribute          ┃    claude-sonnet-5.5    ┃  openrouter/claude-sonnet-5.5  ┃
┡━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Provider           │        Anthropic        │           OpenRouter           │
├────────────────────┼─────────────────────────┼────────────────────────────────┤
│ Source             │         Direct          │           Aggregator           │
├────────────────────┼─────────────────────────┼────────────────────────────────┤
│ Platform Fee       │          0.0%           │              5.5%              │
├────────────────────┼─────────────────────────┼────────────────────────────────┤
│ Context Window     │           1M            │               1M               │
├────────────────────┼─────────────────────────┼────────────────────────────────┤
│ Input Cost         │    2.0000 USD (/1M)     │        2.1100 USD (/1M)        │
├────────────────────┼─────────────────────────┼────────────────────────────────┤
│ Cached Input       │    0.1000 USD (/1M)     │        0.1055 USD (/1M)        │
├────────────────────┼─────────────────────────┼────────────────────────────────┤
│ Output / Unit Cost │    10.0000 USD (/1M)    │       10.5500 USD (/1M)        │
└────────────────────┴─────────────────────────┴────────────────────────────────┘
```

## Supported Models (Curated Frontier + 470+ Live Catalog)

### Flagship Text & Reasoning Models
| Model | Provider | Input/1M | Cached/1M | Output/1M | Context |
|-------|----------|----------|-----------|-----------|---------|
| GPT-6.2 Astra (`gpt-6.2-astra`) | OpenAI | $8.00 | $0.40 | $40.00 | 1.05M |
| GPT-6.2 Sol (`gpt-6.2-sol`) | OpenAI | $2.00 | $0.10 | $10.00 | 1.05M |
| GPT-6.1 Terra (`gpt-6.1-terra`) | OpenAI | $1.00 | $0.05 | $5.00 | 1.05M |
| GPT-6 Luna (`gpt-6-luna`) | OpenAI | $0.10 | $0.01 | $0.50 | 1.05M |
| o3 / o3-Pro (`o3`, `o3-pro`) | OpenAI | $2.00 / $20 | $0.50 / - | $8.00 / $80 | 200K |
| Claude Fable 5.2 (`claude-fable-5.2`) | Anthropic | $8.00 | $0.20 | $40.00 | 1M |
| Claude Opus 5.5 (`claude-opus-5.5`) | Anthropic | $4.00 | $0.20 | $20.00 | 1M |
| Claude Sonnet 5.5 (`claude-sonnet-5.5`) | Anthropic | $2.00 | $0.10 | $10.00 | 1M |
| Claude Haiku 5.5 (`claude-haiku-5.5`) | Anthropic | $0.10 | $0.01 | $0.50 | 1M |
| Gemini 4 Neon (`gemini-4-neon`) | Google | $3.00 | $0.15 | $15.00 | 1M |
| Gemini 4 Carbon / Argon (`gemini-4-carbon`) | Google | $2.00 | $0.10 | $10.00 | 1M |
| Gemini 4 Hydrogen (`gemini-4-hydrogen`) | Google | $1.50 | $0.075 | $7.50 | 1M |
| Gemini 3.8 Flash (`gemini-3.8-flash`) | Google | $0.825 | $0.0825 | $4.125 | 1M |
| Grok 4.7 (`grok-4.7`) | xAI | $2.00 | $0.50 | $6.00 | 500K |
| DeepSeek V4 Pro (`deepseek-v4-pro`) | DeepSeek | $0.90 | $0.20 | $1.50 | 1M |
| DeepSeek V4.1 Flash (`deepseek-v4.1-flash`) | DeepSeek | $0.15 | $0.003 | $0.60 | 1M |
| Qwen 4 Max (`qwen4-max`) | Alibaba Qwen | $1.425 | - | $4.275 | 1M |
| Llama 4 Maverick / Scout (`llama-4-maverick`) | Meta | $0.35 / $0.10 | $0.17 / - | $1.00 / $0.30 | 512K / 1.3M |
| Mistral Large 4 (`mistral-large-4`) | Mistral | $0.70 | - | $2.10 | 1M |
| Kimi K3.1 Pro (`kimi-k3.1-pro`) | Moonshot | $0.253 | - | $8.80 | 1M |
| MiniMax M3.1 Flash (`minimax-m3.1-flash`) | MiniMax | $0.075 | - | $0.30 | 1M |

### Image, Video & Audio Models
| Model | Provider | Price | Billing Unit | Type |
|-------|----------|-------|--------------|------|
| GPT-Image 2.6 Sunburst (`gpt-image-2.6-sunburst`) | OpenAI | $0.08 | per image | Image |
| GPT-Image 2.6 Flare (`gpt-image-2.6-flare`) | OpenAI | $0.025 | per image | Image |
| Imagen 4 Fast / Standard / Ultra | Google | $0.02 / $0.04 / $0.06 | per image | Image |
| Flux 1.1 Pro / Ultra | Black Forest Labs | $0.04 / $0.06 | per image | Image |
| Veo 3.1 Fast / Standard (`veo-3.1`) | Google | $0.10 / $0.40 | per second | Video |
| Lyria 3 Clip / Pro (`lyria-3-pro`) | Google | $0.04 / $0.08 | per clip / song | Music |
| Whisper (`whisper`) | OpenAI | $0.006 | per minute | Speech-to-Text |
| TTS Standard / HD | OpenAI | $15 / $30 | per 1M chars | Text-to-Speech |

> Browse curated models via `aicost list`, include previous-gen models with `--include-legacy`, or query **all 470+ live models** with `aicost list --live`!

## Features

- **Always-Current Hybrid Catalog:** Weekly automated discovery of newly released flagship models + on-demand fallback to **470+ live OpenRouter models** (never hits "Model not found" on new releases).
- **Dynamic Direct vs. Aggregator Math:** Prefix *any* model with `openrouter/` (e.g., `openrouter/gpt-6.2-astra`) to instantly compare Direct billing vs. OpenRouter's 5.5% fee.
- **Prompt Caching & Batch Discounts:** First-class support for `--cached-input` read rates (up to 95% savings) and `--batch` API discounts.
- **Monthly Workload Estimator (`aicost estimate`):** Forecast daily, 30-day, and annual API spend from expected request traffic.
- **200+ Currencies with Offline Resilience:** Powered by a 3-tier CDN currency engine (`TRY`, `EUR`, `GBP`, `AZN`, `AED`, `JPY`, etc.) with 24-hour local cache.
- **Dual MCP Server Ecosystem (`npx` & `uvx`):** Zero-install MCP integration via npm (`aicost-mcp`) or PyPI (`aicost-cli`).

## Installation

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

### Python CLI (`pip` / `uv`)
```bash
pip install -U aicost-cli
```

## CLI Usage

### List & Filter Models
```bash
aicost list --currency TRY
aicost list --provider Anthropic
aicost list --live --provider Cohere
aicost list --tag agentic --sort input --json
```

### Calculate Cost (with Caching & Batch Support)
```bash
# Frontier model with prompt caching
aicost calc claude-opus-5.5 --input 200000 --cached-input 800000 --output 100000 --currency USD

# Batch API (-50%) calculation
aicost calc gpt-6.2-astra --input 1000000 --output 500000 --batch

# Dynamic OpenRouter aggregator fee breakdown on ANY model
aicost calc openrouter/gemini-4-carbon --input 1000000 --output 500000 --currency TRY

# Multimodal unit calculation (seconds, minutes, images)
aicost calc veo-3.1 --units 8 --currency USD
```

### Project Monthly Workload Budget
```bash
aicost estimate claude-sonnet-5.5 --requests-per-day 2500 --input 1800 --output 450 --currency USD
```

### Compare 2+ Models Side-by-Side
```bash
aicost compare gpt-6.2-astra claude-opus-5.5 gemini-4-neon grok-4.7 --currency USD
```

### Get Task Recommendations
```bash
aicost recommend "fast cheap agentic coding" --max-cost 1.0 --currency USD
```

### Sync Latest Pricing, Live 470+ Catalog & Exchange Rates
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
