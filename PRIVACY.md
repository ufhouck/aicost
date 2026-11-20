# Privacy Policy

**Last updated:** November 20, 2026

## Overview

AI-Cost-CLI (`aicost-cli`) and `aicost-mcp` are local-first, open-source tools. We are committed to user privacy and data transparency.

## Data Collection

### What We DO NOT Collect
- ❌ Personal information (name, email, IP address)
- ❌ Usage analytics or telemetry
- ❌ API keys or authentication credentials
- ❌ Token counts, prompts, or AI model usage data
- ❌ Financial or billing information

### What the Tool Does Locally
- ✅ Caches pricing data locally in `~/.aicost/pricing_cache.json`
- ✅ Caches currency exchange rates locally in `~/.aicost/exchange_cache.json`
- ✅ All calculations are performed entirely on your machine

## External Network Requests

Both the Python CLI and the Node.js MCP server make **two types** of outbound HTTPS requests, strictly for fetching publicly available reference data:

| Request | URL | Data Sent | Purpose |
|---------|-----|-----------|---------|
| Currency Rates (Primary) | `cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/` | None | Fetching 200+ exchange rates |
| Currency Rates (Fallback) | `latest.currency-api.pages.dev` / `api.frankfurter.app` | None | Automatic mirror fallback if primary CDN is unreachable |
| Pricing Sync | `raw.githubusercontent.com/ufhouck/aicost/main/data/pricing.json` | None | Fetching latest AI model pricing |

**No cookies, tokens, user identifiers, or personal data** are included in these requests.

## Local Cache

Cached data is shared between `aicost-cli` and `aicost-mcp` in `~/.aicost/` on your machine:

```text
~/.aicost/
├── pricing_cache.json    # Cached model pricing (7-day TTL)
└── exchange_cache.json   # Cached exchange rates (24-hour TTL)
```

You can delete this directory at any time to clear all cached data:
```bash
rm -rf ~/.aicost
```

## MCP Server Mode

When running as an MCP server (`npx -y aicost-mcp` or `aicost mcp`), the tool communicates exclusively via **local stdio** (standard input/output). No network server is started, and no ports are opened.

## Third-Party Services

This project does not integrate with any third-party analytics, advertising, or tracking services.

## Changes to This Policy

Any changes to this privacy policy will be documented in the [CHANGELOG](CHANGELOG.md) and reflected in this file.

## Contact

For privacy-related questions, please open an issue on [GitHub](https://github.com/ufhouck/aicost/issues).
