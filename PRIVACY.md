# Privacy Policy

**Last updated:** April 24, 2026

## Overview

AI-Cost-CLI is a local-first, open-source tool. We are committed to user privacy and data transparency.

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

AI-Cost-CLI makes **two types** of outbound HTTP requests, both for fetching publicly available data:

| Request | URL | Data Sent | Purpose |
|---------|-----|-----------|---------|
| Currency Rates | `cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/` | None | Fetching exchange rates |
| Pricing Sync | `raw.githubusercontent.com/ufhouck/aicost/main/data/pricing.json` | None | Fetching latest AI model pricing |

**No cookies, tokens, user identifiers, or personal data** are included in these requests.

## Local Cache

Cached data is stored in `~/.aicost/` on your machine:

```
~/.aicost/
├── pricing_cache.json    # Cached model pricing (refreshed weekly)
└── exchange_cache.json   # Cached exchange rates (refreshed daily)
```

You can delete this directory at any time to clear all cached data:
```bash
rm -rf ~/.aicost
```

## MCP Server Mode

When running as an MCP server (`aicost mcp`), the tool communicates exclusively via **local stdio** (standard input/output). No network server is started, and no ports are opened.

## Third-Party Services

This project does not integrate with any third-party analytics, advertising, or tracking services.

## Changes to This Policy

Any changes to this privacy policy will be documented in the [CHANGELOG](CHANGELOG.md) and reflected in this file.

## Contact

For privacy-related questions, please open an issue on [GitHub](https://github.com/ufhouck/aicost/issues).
