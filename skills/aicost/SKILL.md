---
name: aicost
description: Lookup AI model costs, currency conversions, and recommend best cost-effective models for tasks.
license: MIT
metadata:
  author: ufhouck
---

# AICost Skill

Use the `aicost` CLI tool to look up current AI model pricing, convert currencies automatically, and recommend/compare models based on a live-updating pricing database.

## When to use

- When the user asks about the price, cost, or pricing of an AI API (like GPT-4o, Claude 4.6, Gemini 3.1, Qwen, Flux 2).
- When the user wants to compare two or more models by cost.
- When the user wants to know the "cheapest" or "best" AI model for a specific task.
- When you (the Agent) are helping the user decide on an AI model based on ROI.

## How to use

Run the following terminal commands to execute the tool:

1. **Verify or Sync Latest Data**:
   `aicost sync`
   *(Always run this if the user asks for the "latest" or "most recent" prices)*

2. **List all models and prices**:
   `aicost list --currency <target-currency>`

3. **Compare two models side-by-side**:
   `aicost compare <model1-id> <model2-id> --currency <target-currency>`

4. **Calculate a specific model's cost**:
   `aicost calc <model-id> --input <tokens> --output <tokens> --currency <target-currency>`

5. **Recommend models based on a task**:
   `aicost recommend "<task description>" --currency <target-currency>`

### Prerequisites
The `aicost` CLI should be installed on the system. If not found, refer the user to the [Installation Guide](https://github.com/ufhouck/aicost#installation).
