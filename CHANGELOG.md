# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- LICENSE file (MIT)
- SECURITY.md — Vulnerability reporting policy
- PRIVACY.md — Data transparency documentation
- CODE_OF_CONDUCT.md — Contributor Covenant v2.1
- CONTRIBUTING.md — Contribution guidelines
- GitHub Issue Templates (Bug Report, Feature Request, Pricing Update)
- README badges (License, Python, MCP)

### Changed
- Updated pricing database date to 2026-04-24
- Improved `.gitignore` for comprehensive Python project coverage
- Enhanced `pyproject.toml` with license, classifiers, keywords, and URLs

## [1.0.0] - 2026-04-10

### Added
- Initial release
- `aicost list` — List all models with pricing
- `aicost calc` — Calculate cost for specific usage
- `aicost compare` — Side-by-side model comparison
- `aicost recommend` — Task-based model recommendations
- `aicost sync` — Manual pricing data sync from GitHub
- `aicost report-price` — Generate GitHub issue for pricing updates
- `aicost mcp` — MCP server for AI agent integration
- Real-time currency conversion (USD, TRY, EUR, etc.)
- Automated weekly pricing sync via GitHub Actions
- Support for Direct, Aggregator, and Gateway provider types
- Platform fee transparency for aggregators (e.g., OpenRouter 5.5%)
