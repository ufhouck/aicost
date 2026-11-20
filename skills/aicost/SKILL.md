---
name: aicost
description: Lookup AI model costs, prompt-caching/batch discounts, monthly workload budgets, currency conversions, and cost-effective model recommendations.
license: MIT
metadata:
  author: ufhouck
---

# AICost Skill

Use the `aicost` CLI tool to look up current AI model pricing, factor in prompt caching and Batch API discounts, project monthly production budgets, convert across 200+ currencies, and compare/recommend models. Pass `--json` to any command when structured machine-readable output is preferred.

## When to use

- When the user asks about the price, cost, or pricing of an AI API (like GPT-5.5, Claude Opus 4.7, Gemini 3.1, DeepSeek R1).
- When the user wants to compare two or more models side-by-side (including Direct vs. OpenRouter fees).
- When the user wants to project daily, monthly, or annual API spend for a recurring workload.
- When the user wants to know the "cheapest" or "best" AI model for a specific task.
- When the user asks about image, video, or audio generation costs (Imagen, Veo, Lyria, DALL-E, Whisper, TTS).

## How to use

Run the following terminal commands (append `--json` for structured JSON output):

1. **Verify or Sync Latest Data & Exchange Rates**:
   `aicost sync`
   *(Run this if the user asks for the "latest" or "most recent" prices)*

2. **List and filter models**:
   `aicost list --currency <currency> [--provider <name>] [--type text|image|video|audio] [--tag <tag>] [--hide-legacy] [--json]`

3. **Compare two or more models side-by-side**:
   `aicost compare <model1> <model2> [<model3> ...] --currency <currency> [--json]`

4. **Calculate a specific call's cost**:
   `aicost calc <model-id> --input <tokens> [--cached-input <tokens>] --output <tokens> [--batch] --currency <currency> [--json]`
   For image/video/audio/gateway models, pass `--units <count>` instead of token flags.

5. **Estimate monthly/annual production budget**:
   `aicost estimate <model-id> --requests-per-day <num> --input <avg_in> --output <avg_out> --currency <currency> [--json]`

6. **Recommend models based on a task**:
   `aicost recommend "<task description>" [--type <type>] [--max-cost <usd>] --currency <currency> [--json]`

### Prerequisites
The `aicost` CLI (`pip install aicost-cli`) must be pre-installed on the system, or the `aicost-mcp` MCP server (`npx -y aicost-mcp`) can be configured in the MCP client.
