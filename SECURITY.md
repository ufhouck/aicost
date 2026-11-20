# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability within AI-Cost-CLI or `aicost-mcp`, please report it responsibly.

### How to Report

1. **Do NOT** open a public GitHub issue for security vulnerabilities.
2. Instead, please use [GitHub's private vulnerability reporting](https://github.com/ufhouck/aicost/security/advisories/new).
3. Provide a detailed description of the vulnerability and steps to reproduce it.

### What to Expect

- **Acknowledgment:** We will acknowledge your report within 48 hours.
- **Assessment:** We will assess the vulnerability and determine its impact.
- **Fix Timeline:** Critical vulnerabilities will be patched within 7 days. Non-critical issues will be addressed in the next scheduled release.
- **Credit:** We will credit you in the release notes (unless you prefer to remain anonymous).

## Security Considerations

AI-Cost-CLI (`aicost-cli`) and the npm MCP server (`aicost-mcp`) make the following external network requests over HTTPS:

| Request | Destination | Purpose |
|---------|-------------|---------|
| Currency rates (Primary) | `cdn.jsdelivr.net` (`@fawazahmed0/currency-api`) | Real-time currency conversion (200+ currencies) |
| Currency rates (Fallback) | `latest.currency-api.pages.dev` / `api.frankfurter.app` | Resilient exchange rate fallback |
| Pricing sync | `raw.githubusercontent.com` | Fetching latest curated model pricing |
| Live catalog fallback | `openrouter.ai/api/v1/models` | Public unauthenticated catalog of 470+ live models |

- **No authentication tokens or API keys** are transmitted.
- **No personal data** is collected or sent.
- All data is cached locally in `~/.aicost/` and can be deleted at any time.

## Dependencies

We keep dependencies minimal across both ecosystems:

**Python (`aicost-cli`):**
- `typer` — CLI framework
- `rich` — Terminal formatting
- `requests` — HTTP client
- `mcp` — Model Context Protocol server

**Node.js (`aicost-mcp`):**
- `@modelcontextprotocol/sdk` — Official MCP server SDK
- `zod` — Schema validation
