---
name: aicost
description: Lookup AI model costs, currency conversions, and recommend best cost-effective models for tasks.
license: MIT
metadata:
  author: ufhouck
---

# AICost Skill

Use the `aicost` CLI tool to look up current AI model pricing, convert currencies automatically, and recommend the best Models to the user for specific tasks based on the `pricing.json` database.

## When to use

- When the user asks about the price, cost, or pricing of an AI API (like GPT-4o, Claude 4.6, Gemini 3.1, Flux 2).
- When the user wants to know the "cheapest" or "best" AI model for a specific task.
- When you (the Agent) are helping the user decide which AI model API to integrate into their software project based on cost.

## How to use

Run the following terminal commands to execute the tool:

1. **List all models and prices**:
   `aicost list --currency USD`

2. **Calculate a specific model's cost based on tokens**:
   `aicost calc <model-id> <input-tokens> <output-tokens> --currency <target-currency>`
   *(Example: `aicost calc gpt-4o-mini 1000000 500000 --currency TRY`)*

3. **Recommend models based on a task description**:
   `aicost recommend "<task description>" --currency <target-currency>`
   *(Example: `aicost recommend "fast premium ocr" --currency EUR`)*

### Prerequisites
The `aicost` CLI should be installed on the system where the agent is running. If not found, please refer to the official [Installation Guide](https://github.com/ufhouck/aicost#installation).
