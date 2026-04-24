# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability within AI-Cost-CLI, please report it responsibly.

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

AI-Cost-CLI makes the following external network requests:

| Request | Destination | Purpose |
|---------|-------------|---------|
| Currency rates | `cdn.jsdelivr.net` (Fawaz Ahmed API) | Real-time currency conversion |
| Pricing sync | `raw.githubusercontent.com` | Fetching latest model pricing |

- **No authentication tokens or API keys** are transmitted.
- **No personal data** is collected or sent.
- All data is cached locally in `~/.aicost/` and can be deleted at any time.

## Dependencies

We keep dependencies minimal:
- `typer` — CLI framework
- `rich` — Terminal formatting
- `requests` — HTTP client
- `mcp` (optional) — Model Context Protocol server
