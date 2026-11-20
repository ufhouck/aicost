# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-11-20

### Added
- **Official npm MCP Package (`aicost-mcp`)** — Zero-install TypeScript MCP server (`npx -y aicost-mcp`) sharing `~/.aicost/` cache and full feature parity with Python
- **`aicost estimate` command** — Daily, monthly, and annual API budget projections for recurring production workloads
- **Prompt Caching & Batch API Support** — Added `cost_per_1m_cached_input_tokens` (`--cached-input`) and `batch_discount` (`--batch`) calculations
- **Schema v2.0 Metadata** — Added explicit `billing_unit`, `context_window`, `aliases`, and `openrouter_id` fields across all 29 models
- **JSON Output Mode (`--json`)** — Structured JSON output across `list`, `calc`, `compare`, `recommend`, `estimate`, and `sync`
- **Rich Filtering & Sorting** — `aicost list` now supports `--provider`, `--type`, `--tag`, `--sort`, and `--hide-legacy`
- **Multi-Model Comparison** — `aicost compare` and MCP `compare_ai_models` now compare 2 or more models side-by-side
- **Smart Model Aliases & Fuzzy Suggestions** — Shorthand aliases (`opus-4.7`, `r1`, `flash-lite`, etc.) and "Did you mean?" suggestions
- **Expanded MCP Tooling & Resources** — Added `list_ai_models`, `calculate_ai_cost`, `estimate_monthly_cost`, `sync_pricing_data`, and `aicost://pricing/*` resources
- **`aicost --version`** CLI flag and `aicost-mcp` script entry point
- **Automated `pytest` & GitHub Actions CI (`ci.yml`)** — Validates pricing schema, calculation math, wheel contents, and TypeScript MCP build

### Fixed
- **Wheel Packaging Bug** — Bundled `data/pricing.json` inside the PyPI `.whl` archive via Hatchling `force-include` so fresh `pip install aicost-cli` works immediately offline
- **Aggregator Platform Fee Calculation** — Fixed `calc`, `list`, and `mcp` to accurately add `platform_fee` on top of base token costs
- **Currency Cache Directory Creation** — Fixed missing `~/.aicost` directory creation and upgraded to a 3-tier CDN currency engine (`@fawazahmed0/currency-api` + Cloudflare mirror + ECB fallback) supporting 200+ currencies
- **Pricing Sync Substring Collisions** — Replaced substring matching in `scripts/automate_pricing.py` with exact `openrouter_id` matching
- **MCP `uvx` Compatibility** — Included `mcp` dependency for Python 3.10+ with a lightweight built-in stdio JSON-RPC fallback for Python 3.9

## [1.1.1] - 2026-04-24

### Changed
- Updated GitHub Actions workflows (`actions/checkout@v5`, `actions/setup-python@v6`) for Node.js 24 compatibility and PyPI Trusted Publisher release verification

## [1.1.0] - 2026-04-24

### Added
- **Claude Opus 4.7** — Anthropic's next-gen flagship ($5/$25 per 1M tokens)
- **GPT-5.5** — OpenAI's natively omnimodal flagship ($5/$30 per 1M tokens)
- **GPT-5.5 Pro** — OpenAI's maximum precision variant ($30/$180 per 1M tokens)
- **Gemini 3.1 Flash-Lite** — Google's fastest budget model ($0.25/$1.50 per 1M tokens)
- **Gemini 2.5 Flash** — Previous-gen hybrid reasoning model ($0.30/$2.50 per 1M tokens)
- **DeepSeek V3** — Latest general-purpose model ($0.14/$0.28 per 1M tokens)
- **DeepSeek R1** — Advanced reasoning model ($0.55/$2.19 per 1M tokens)
- **Imagen 4** family — Google image generation (Fast $0.02, Standard $0.04, Ultra $0.06 per image)
- **Veo 3** family — Google video generation (Lite $0.05/sec, Standard $0.40/sec)
- **Lyria 3** family — Google music generation (Clip $0.04, Pro $0.08 per song)
- **DALL-E 3** — OpenAI image generation ($0.04/image standard)
- **GPT-Image-1** — OpenAI budget image generation ($0.02/image)
- **Whisper** — OpenAI speech-to-text ($0.006/minute)
- **TTS Standard/HD** — OpenAI text-to-speech ($15/$30 per 1M characters)
- `legacy` tag for older flagship models (Claude Opus 4.6, GPT-4o, DeepSeek Coder V2)
- `agentic` tag for models optimized for autonomous workflows
- LICENSE file (MIT), SECURITY.md, PRIVACY.md, CODE_OF_CONDUCT.md, CONTRIBUTING.md, and GitHub Issue Templates

### Changed
- Updated pricing database date to 2026-04-24
- Improved `.gitignore` and `pyproject.toml` metadata

## [1.0.0] - 2026-04-10

### Added
- Initial release (`list`, `calc`, `compare`, `recommend`, `sync`, `report-price`, `mcp`)
