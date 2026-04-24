# AI-Cost-CLI

[![PyPI](https://img.shields.io/pypi/v/aicost-cli.svg)](https://pypi.org/project/aicost-cli/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![MCP Registry](https://img.shields.io/badge/MCP-Registry-green.svg)](https://registry.modelcontextprotocol.io)

A terminal-based calculator and recommendation engine for AI API costs. Supports multiple providers, local currency conversion, and automated pricing updates.

<!-- mcp-name: io.github.ufhouck/aicost-cli -->

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

## Supported Models

### Text Models
| Model | Provider | Input/1M | Output/1M | Tags |
|-------|----------|----------|-----------|------|
| Claude Opus 4.7 | Anthropic | $5.00 | $25.00 | reasoning, coding, vision, agentic |
| GPT-5.5 | OpenAI | $5.00 | $30.00 | multimodal, coding, agentic |
| GPT-5.5 Pro | OpenAI | $30.00 | $180.00 | precision, enterprise, agentic |
| Claude Sonnet 4.6 | Anthropic | $3.00 | $15.00 | coding, fast, general |
| GPT-4o | OpenAI | $2.50 | $10.00 | reasoning, coding, vision |
| Gemini 3.1 Pro | Google | $2.00 | $12.00 | long-context, multimodal |
| DeepSeek R1 | DeepSeek | $0.55 | $2.19 | reasoning, coding, smart |
| Gemini 2.5 Flash | Google | $0.30 | $2.50 | fast, reasoning, legacy |
| Gemini 3.1 Flash-Lite | Google | $0.25 | $1.50 | fast, cheap, agentic |
| DeepSeek V3 | DeepSeek | $0.14 | $0.28 | general, coding, cheap |

### Image, Video & Audio Models
| Model | Provider | Price | Type |
|-------|----------|-------|------|
| Imagen 4 Fast | Google | $0.02/image | Image |
| GPT-Image-1 | OpenAI | $0.02/image | Image |
| DALL-E 3 | OpenAI | $0.04/image | Image |
| Imagen 4 Ultra | Google | $0.06/image | Image |
| Veo 3 Lite | Google | $0.05/sec | Video |
| Veo 3 | Google | $0.40/sec | Video |
| Lyria 3 Clip | Google | $0.04/clip | Music |
| Lyria 3 Pro | Google | $0.08/song | Music |
| Whisper | OpenAI | $0.006/min | Speech-to-Text |
| TTS Standard | OpenAI | $15/1M chars | Text-to-Speech |

> Full list available via `aicost list --currency USD`

## Features

- **Infrastructure Comparison:** Compare **Direct** providers vs. **Aggregators** (OpenRouter) and **Gateways** (Portkey, LiteLLM, Martian).
- **Transparent Commissions:** Automatically calculates platform fees (e.g., OpenRouter's 5.5% credit fee).
- **Direct Cost Calculation:** Full breakdown of base costs and platform middle-layer fees.
- **Currency Conversion:** Real-time conversion to local currencies (TRY, EUR, etc.) with offline fallback.
- **Automated Pricing:** Weekly automated updates from official provider documentation.
- **MCP Server:** Native support for AI agents (Cursor, Claude Desktop).

## Installation

```bash
pip install aicost-cli
```

With MCP server support:
```bash
pip install aicost-cli[mcp]
```

Or from source:
```bash
git clone https://github.com/ufhouck/aicost.git
cd aicost
pip install -e .
```

## Usage

### List All Models
```bash
aicost list --currency TRY
```

### Calculate Cost
```bash
# Text model — token-based
aicost calc claude-opus-4.7 --input 1000000 --output 500000 --currency TRY

# With platform fee breakdown (aggregators)
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

### Compare Models
```bash
aicost compare claude-opus-4.7 gpt-5.5 --currency USD
```

### Get Recommendations
```bash
aicost recommend "fast cheap coding" --currency USD
```

### Sync Latest Pricing
```bash
aicost sync
```

## MCP Server

Start the Model Context Protocol server for AI agent integration:
```bash
aicost mcp
```

## Registries
- [PyPI](https://pypi.org/project/aicost-cli/)
- [MCP Registry](https://registry.modelcontextprotocol.io) — `io.github.ufhouck/aicost-cli`
- [Smithery.ai](https://smithery.ai/skills/ufhouck-oskt/aicost)
- [Skills.sh](https://skills.sh/ufhouck/aicost/aicost)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute, including pricing updates, bug reports, and code contributions.

## Community

- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security Policy](SECURITY.md)
- [Privacy Policy](PRIVACY.md)
- [Changelog](CHANGELOG.md)

## License

MIT — see [LICENSE](LICENSE) for details. Developed by [Ufuk Aydın](https://ufukaydin.com).

