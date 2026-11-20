# aicost-mcp

[![npm version](https://img.shields.io/npm/v/aicost-mcp.svg)](https://www.npmjs.com/package/aicost-mcp)
[![MCP Registry](https://img.shields.io/badge/MCP-Registry-green.svg)](https://registry.modelcontextprotocol.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Official **Model Context Protocol (MCP)** server for [AI-Cost-CLI](https://github.com/ufhouck/aicost) — calculate AI API costs across **60+ curated multimodal models** (`GPT-6.2`, `Claude 5.5 / Fable 5.2`, `Gemini 4`, `Grok 4.7`, `DeepSeek V4`, `Llama 4`, `Qwen 4`, `Mistral Large 4`, `GPT-Image 2.6`, `Veo 3.1`, `Flux`) plus **470+ live OpenRouter models**, project monthly budgets, and convert across **200+ local currencies** directly inside Claude Desktop, Cursor, Windsurf, VS Code, Cline, or Antigravity.

## Quick Start (`npx`)

Add `aicost-mcp` to your MCP client configuration (`claude_desktop_config.json`, `.cursor/mcp.json`, or `mcp_config.json`):

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

No API keys required. Includes an offline-ready curated database bundled inside the package, automatic weekly model discovery, live 470+ OpenRouter catalog fallback, and local `~/.aicost/` caching.

## Available MCP Tools

| Tool | Description |
|------|-------------|
| `list_ai_models` | List & filter curated models (or `include_live: true` for 470+ live models) by `provider`, `model_type`, `tag`, and `currency`. |
| `calculate_ai_cost` | Exact cost calculation with prompt-caching (`cached_input_tokens`), Batch API discount (`batch`), and dynamic `openrouter/<model>` fee breakdown. |
| `compare_ai_models` | Side-by-side comparison of 2+ models across pricing, context window, platform fees, and sample workloads. |
| `recommend_ai_model` | Task-based cost-effective model recommendations (`coding`, `cheap`, `fast`, `agentic`, `vision`, `video`, `music`). |
| `estimate_monthly_cost` | Daily, monthly, and annual API spend projections for production request volumes. |
| `sync_pricing_data` | Refresh curated pricing, 470+ live models, and 200+ currency exchange rates. |
| `get_pricing_metadata` | Check database schema version, model counts, and cache timestamps. |

## Available MCP Resources

- `aicost://pricing/models` — Full JSON pricing catalog
- `aicost://pricing/metadata` — Database, live catalog, and exchange rate cache status

## Python CLI Companion

```bash
pip install -U aicost-cli
aicost list --currency TRY
```

## License

MIT — Developed by [Ufuk Aydın](https://ufukaydin.com).
