# aicost-mcp

[![npm version](https://img.shields.io/npm/v/aicost-mcp.svg)](https://www.npmjs.com/package/aicost-mcp)
[![MCP Registry](https://img.shields.io/badge/MCP-Registry-green.svg)](https://registry.modelcontextprotocol.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Official **Model Context Protocol (MCP)** server for [AI-Cost-CLI](https://github.com/ufhouck/aicost) — calculate AI API costs, compare providers (Direct vs. OpenRouter/Gateways), project monthly budgets, and convert across **200+ local currencies** directly inside Claude Desktop, Cursor, Windsurf, VS Code, Cline, or Antigravity.

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

No API keys required. Includes an offline-ready pricing database bundled inside the package with live GitHub updates and local `~/.aicost/` caching.

## Available MCP Tools

| Tool | Description |
|------|-------------|
| `list_ai_models` | List & filter models by `provider`, `model_type` (`text`, `image`, `video`, `audio`, `gateway`), `tag`, and `currency`. |
| `calculate_ai_cost` | Exact cost calculation with prompt-caching (`cached_input_tokens`), Batch API discount (`batch`), and aggregator `platform_fee` breakdown. |
| `compare_ai_models` | Side-by-side comparison of 2+ models across pricing, context window, platform fees, and sample workloads. |
| `recommend_ai_model` | Task-based cost-effective model recommendations (`coding`, `cheap`, `fast`, `agentic`, `vision`, `video`, `music`). |
| `estimate_monthly_cost` | Daily, monthly, and annual API spend projections for production request volumes. |
| `sync_pricing_data` | Refresh the latest pricing database from GitHub and update 200+ currency exchange rates. |
| `get_pricing_metadata` | Check database schema version, model count, and cache timestamps. |

## Available MCP Resources

- `aicost://pricing/models` — Full JSON pricing catalog
- `aicost://pricing/metadata` — Database and exchange rate cache status

## Python CLI Companion

Need a rich terminal interface too? Install the companion Python CLI:

```bash
pip install aicost-cli
aicost list --currency TRY
```

## License

MIT — Developed by [Ufuk Aydın](https://ufukaydin.com).
