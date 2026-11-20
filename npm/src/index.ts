#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import {
  calculateCostBreakdown,
  estimateMonthlyCost,
  filterModels,
  findModelById,
  formatUnitLabel,
  getEffectiveRates,
  recommendModels,
  suggestSimilarModels,
} from "./calculator.js";
import { getCurrencyDate, getExchangeRate, refreshRates } from "./currency.js";
import {
  fetchLiveCatalog,
  fetchRemotePricing,
  getAllPricingData,
  getLiveCatalog,
  getPricingMetadata,
  getPricingModels,
} from "./data.js";
import type { ModelEntry } from "./types.js";

const SERVER_VERSION = "1.3.0";

const cliArgs = process.argv.slice(2);
if (cliArgs.includes("--version") || cliArgs.includes("-v")) {
  process.stdout.write(`aicost-mcp v${SERVER_VERSION}\n`);
  process.exit(0);
}
if (cliArgs.includes("--help") || cliArgs.includes("-h")) {
  process.stdout.write(
    `aicost-mcp v${SERVER_VERSION} — Model Context Protocol (MCP) Server for AI API Cost Calculation\n\n` +
      `Usage (MCP Client Config):\n` +
      `  npx -y aicost-mcp\n`
  );
  process.exit(0);
}

function roundNum(val: number | null, decimals = 6): number | null {
  if (val === null) return null;
  const factor = 10 ** decimals;
  return Math.round(val * factor) / factor;
}

async function resolveModelWithLiveFallback(modelId: string): Promise<{
  model?: ModelEntry;
  suggestions: string[];
}> {
  const curated = await getPricingModels(false);
  const directHit = findModelById(curated, modelId);
  if (directHit) {
    return { model: directHit, suggestions: [] };
  }

  const liveModels = await getLiveCatalog(true);
  const liveHit = findModelById(curated, modelId, liveModels);
  if (liveHit) {
    return { model: liveHit, suggestions: [] };
  }

  return {
    suggestions: suggestSimilarModels([...curated, ...liveModels], modelId),
  };
}

const server = new McpServer({
  name: "aicost-mcp",
  version: SERVER_VERSION,
});

// Resource 1: Complete JSON catalog
server.registerResource(
  "pricing-models",
  "aicost://pricing/models",
  {
    title: "AI Models Pricing Catalog",
    description:
      "Complete JSON catalog of AI model prices, context windows, billing units, and platform fees.",
    mimeType: "application/json",
  },
  async (uri) => {
    const db = await getAllPricingData();
    return {
      contents: [
        {
          uri: uri.href,
          mimeType: "application/json",
          text: JSON.stringify(db, null, 2),
        },
      ],
    };
  }
);

// Resource 2: Pricing & Currency Metadata
server.registerResource(
  "pricing-metadata",
  "aicost://pricing/metadata",
  {
    title: "Pricing & Currency Metadata",
    description:
      "Current pricing database version, last update date, live catalog count, and currency rate cache timestamp.",
    mimeType: "application/json",
  },
  async (uri) => {
    const meta = await getPricingMetadata();
    return {
      contents: [
        {
          uri: uri.href,
          mimeType: "application/json",
          text: JSON.stringify(
            {
              ...meta,
              currency_cached_at: getCurrencyDate(),
              server_version: SERVER_VERSION,
            },
            null,
            2
          ),
        },
      ],
    };
  }
);

// Tool 1: list_ai_models
server.registerTool(
  "list_ai_models",
  {
    description:
      "List AI models and their effective pricing across text, image, video, audio, and gateway providers. Supports curated flagship models plus optional 400+ live OpenRouter catalog.",
    inputSchema: {
      provider: z
        .string()
        .optional()
        .describe(
          "Filter by provider name (e.g., 'OpenAI', 'Anthropic', 'Google', 'xAI', 'DeepSeek', 'Meta', 'Mistral', 'OpenRouter')"
        ),
      model_type: z
        .enum(["text", "image", "video", "audio", "gateway"])
        .optional()
        .describe("Filter by modality/model type"),
      tag: z
        .string()
        .optional()
        .describe(
          "Filter by capability tag (e.g., 'coding', 'cheap', 'fast', 'agentic', 'vision', 'reasoning', 'long-context')"
        ),
      include_legacy: z
        .boolean()
        .optional()
        .describe("Include older/superseded models tagged as legacy (default: false)"),
      include_live: z
        .boolean()
        .optional()
        .describe("Include 400+ live models from OpenRouter catalog (default: false)"),
      currency: z
        .string()
        .optional()
        .describe("Target currency code (e.g., 'USD', 'TRY', 'EUR', 'GBP'). Defaults to 'USD'."),
    },
  },
  async ({ provider, model_type, tag, include_legacy, include_live, currency }) => {
    try {
      const allModels = await getPricingModels(include_live ?? false);
      const filtered = filterModels(allModels, {
        provider,
        modelType: model_type,
        tag,
        includeLegacy: include_legacy ?? false,
      });
      const { rate, currency: curr } = await getExchangeRate(currency);
      const meta = await getPricingMetadata();

      const payload = {
        currency: curr,
        last_updated: meta.last_updated,
        count: filtered.length,
        models: filtered.map((m) => {
          const eff = getEffectiveRates(m);
          return {
            id: m.id,
            provider: m.provider,
            type: m.type ?? "text",
            source_type: m.source_type ?? "direct",
            billing_unit: m.billing_unit,
            context_window: m.context_window,
            platform_fee: eff.platform_fee,
            effective_input_per_1m:
              eff.input_per_1m !== null ? roundNum(eff.input_per_1m * rate, 6) : null,
            effective_cached_input_per_1m:
              eff.cached_input_per_1m !== null ? roundNum(eff.cached_input_per_1m * rate, 6) : null,
            effective_output_per_1m:
              eff.output_per_1m !== null ? roundNum(eff.output_per_1m * rate, 6) : null,
            effective_unit_cost: eff.per_unit !== null ? roundNum(eff.per_unit * rate, 6) : null,
            fixed_monthly_cost: eff.monthly !== null ? roundNum(eff.monthly * rate, 2) : null,
            tags: m.tags ?? [],
          };
        }),
      };

      return { content: [{ type: "text", text: JSON.stringify(payload, null, 2) }] };
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      return { content: [{ type: "text", text: `Error listing models: ${message}` }], isError: true };
    }
  }
);

const costInputSchema = {
  model_id: z
    .string()
    .describe(
      "Model ID or alias (e.g., 'gpt-6.2-astra', 'claude-opus-5.5', 'gemini-4-carbon', 'grok-4.7', 'deepseek-v4.1-flash', 'veo-3.1')"
    ),
  input_tokens: z.number().int().optional().describe("Uncached input tokens (for text models)"),
  cached_input_tokens: z
    .number()
    .int()
    .optional()
    .describe("Cached input tokens billed at cache-read rate"),
  output_tokens: z
    .number()
    .int()
    .optional()
    .describe("Output completion tokens (for text models)"),
  units: z
    .number()
    .optional()
    .describe(
      "Number of units for non-text models (images, seconds, minutes, songs, clips, 1M chars, or months)"
    ),
  batch: z
    .boolean()
    .optional()
    .describe("Apply Batch API discount if supported (default: false)"),
  currency: z.string().optional().describe("Target currency code (default: 'USD')"),
};

async function handleCalculateCost(args: {
  model_id: string;
  input_tokens?: number;
  cached_input_tokens?: number;
  output_tokens?: number;
  units?: number;
  batch?: boolean;
  currency?: string;
}) {
  try {
    const { model: found, suggestions } = await resolveModelWithLiveFallback(args.model_id);
    if (!found) {
      const hint = suggestions.length > 0 ? ` Did you mean: ${suggestions.join(", ")}?` : "";
      return {
        content: [{ type: "text" as const, text: `Error: Model '${args.model_id}' not found.${hint}` }],
        isError: true,
      };
    }

    const bd = calculateCostBreakdown(found, {
      inputTokens: args.input_tokens,
      cachedInputTokens: args.cached_input_tokens,
      outputTokens: args.output_tokens,
      units: args.units,
      batch: args.batch,
    });
    const { rate, currency: curr } = await getExchangeRate(args.currency);

    const payload = {
      model_id: bd.model_id,
      provider: bd.provider,
      source_type: bd.source_type,
      usage_summary: bd.usage_summary,
      currency: curr,
      is_custom_pricing: bd.is_custom_pricing,
      base_cost: roundNum(bd.base_usd * rate, 6),
      batch_applied: bd.batch_applied,
      batch_savings: roundNum(bd.batch_savings_usd * rate, 6),
      platform_fee_rate: bd.platform_fee_rate,
      platform_fee_cost: roundNum(bd.platform_fee_usd * rate, 6),
      total_cost: roundNum(bd.total_usd * rate, 6),
    };

    return { content: [{ type: "text" as const, text: JSON.stringify(payload, null, 2) }] };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return {
      content: [{ type: "text" as const, text: `Error calculating cost: ${message}` }],
      isError: true,
    };
  }
}

// Tool 2: calculate_ai_cost
server.registerTool(
  "calculate_ai_cost",
  {
    description:
      "Calculate the exact cost of an AI API call with full base cost, prompt-caching, batch discount, and aggregator platform fee breakdown. Supports 60+ curated models and 400+ live OpenRouter models.",
    inputSchema: costInputSchema,
  },
  handleCalculateCost
);

// Tool 3: get_ai_cost (backwards-compatible alias)
server.registerTool(
  "get_ai_cost",
  {
    description:
      "Alias for calculate_ai_cost: calculate the cost of an AI model usage based on tokens or units.",
    inputSchema: costInputSchema,
  },
  handleCalculateCost
);

// Tool 4: compare_ai_models
server.registerTool(
  "compare_ai_models",
  {
    description:
      "Compare two or more AI models side-by-side on pricing, platform fees, context window, and optional sample workload cost.",
    inputSchema: {
      model_ids: z
        .array(z.string())
        .optional()
        .describe(
          "List of two or more model IDs to compare (e.g., ['gpt-6.2-astra', 'claude-opus-5.5', 'gemini-4-neon'])"
        ),
      model_id_1: z.string().optional().describe("First model ID (legacy 2-model parameter)"),
      model_id_2: z.string().optional().describe("Second model ID (legacy 2-model parameter)"),
      input_tokens: z
        .number()
        .int()
        .optional()
        .describe("Optional sample input tokens to compare actual call cost"),
      output_tokens: z
        .number()
        .int()
        .optional()
        .describe("Optional sample output tokens to compare actual call cost"),
      units: z
        .number()
        .optional()
        .describe("Optional sample units to compare non-text call cost"),
      currency: z.string().optional().describe("Target currency code (default: 'USD')"),
    },
  },
  async ({ model_ids, model_id_1, model_id_2, input_tokens, output_tokens, units, currency }) => {
    try {
      const ids = [...(model_ids ?? [])];
      if (ids.length === 0) {
        if (model_id_1) ids.push(model_id_1);
        if (model_id_2) ids.push(model_id_2);
      }
      if (ids.length < 2) {
        return {
          content: [
            {
              type: "text",
              text: "Error: Provide at least two models via 'model_ids' (or 'model_id_1' and 'model_id_2').",
            },
          ],
          isError: true,
        };
      }

      const resolved: ModelEntry[] = [];
      for (const mid of ids) {
        const { model: found, suggestions } = await resolveModelWithLiveFallback(mid);
        if (!found) {
          const hint = suggestions.length > 0 ? ` Did you mean: ${suggestions.join(", ")}?` : "";
          return {
            content: [{ type: "text", text: `Error: Model '${mid}' not found.${hint}` }],
            isError: true,
          };
        }
        resolved.push(found);
      }

      const { rate, currency: curr } = await getExchangeRate(currency);
      const hasWorkload =
        (input_tokens ?? 0) > 0 || (output_tokens ?? 0) > 0 || (units ?? 0) > 0;

      const comparison = resolved.map((m) => {
        const eff = getEffectiveRates(m);
        const unitLbl = formatUnitLabel(m.billing_unit, m.type ?? "text");
        const entry: Record<string, unknown> = {
          id: m.id,
          provider: m.provider,
          source_type: m.source_type ?? "direct",
          platform_fee: eff.platform_fee,
          type: m.type ?? "text",
          billing_unit: unitLbl,
          context_window: m.context_window,
          effective_input_per_1m:
            eff.input_per_1m !== null ? roundNum(eff.input_per_1m * rate, 6) : null,
          effective_cached_input_per_1m:
            eff.cached_input_per_1m !== null ? roundNum(eff.cached_input_per_1m * rate, 6) : null,
          effective_output_per_1m:
            eff.output_per_1m !== null ? roundNum(eff.output_per_1m * rate, 6) : null,
          effective_unit_cost: eff.per_unit !== null ? roundNum(eff.per_unit * rate, 6) : null,
          fixed_monthly_cost: eff.monthly !== null ? roundNum(eff.monthly * rate, 2) : null,
          tags: m.tags ?? [],
        };
        if (hasWorkload) {
          const bd = calculateCostBreakdown(m, {
            inputTokens: input_tokens,
            outputTokens: output_tokens,
            units,
          });
          entry.sample_workload_cost = roundNum(bd.total_usd * rate, 6);
        }
        return entry;
      });

      return {
        content: [{ type: "text", text: JSON.stringify({ currency: curr, comparison }, null, 2) }],
      };
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      return {
        content: [{ type: "text", text: `Error comparing models: ${message}` }],
        isError: true,
      };
    }
  }
);

// Tool 5: recommend_ai_model
server.registerTool(
  "recommend_ai_model",
  {
    description:
      "Recommend the best cost-effective AI models for a task description. Supports keywords like 'coding', 'cheap', 'fast', 'agentic', 'vision', 'reasoning', 'video', 'image', 'music'.",
    inputSchema: {
      task_description: z.string().describe("Description of the workload or task"),
      limit: z.number().int().optional().describe("Maximum number of recommendations (default: 3)"),
      model_type: z
        .enum(["text", "image", "video", "audio", "gateway"])
        .optional()
        .describe("Optional modality filter"),
      max_input_cost: z
        .number()
        .optional()
        .describe("Optional maximum USD cost per 1M input tokens (or per unit)"),
      include_legacy: z
        .boolean()
        .optional()
        .describe("Include legacy models (default: false)"),
      currency: z.string().optional().describe("Target currency code (default: 'USD')"),
    },
  },
  async ({ task_description, limit, model_type, max_input_cost, include_legacy, currency }) => {
    try {
      const allModels = await getPricingModels(false);
      const recs = recommendModels(allModels, {
        taskDescription: task_description,
        limit: limit ?? 3,
        modelType: model_type,
        maxInputCost: max_input_cost,
        includeLegacy: include_legacy ?? false,
      });

      if (recs.length === 0) {
        return {
          content: [{ type: "text", text: "No suitable models matched the given task and constraints." }],
        };
      }

      const { rate, currency: curr } = await getExchangeRate(currency);
      const formatted = recs.map((m, i) => {
        const eff = getEffectiveRates(m);
        return {
          rank: i + 1,
          id: m.id,
          provider: m.provider,
          type: m.type ?? "text",
          description: m.description ?? "",
          tags: m.tags ?? [],
          effective_input_per_1m:
            eff.input_per_1m !== null ? roundNum(eff.input_per_1m * rate, 6) : null,
          effective_output_per_1m:
            eff.output_per_1m !== null ? roundNum(eff.output_per_1m * rate, 6) : null,
          effective_unit_cost: eff.per_unit !== null ? roundNum(eff.per_unit * rate, 6) : null,
        };
      });

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(
              { task: task_description, currency: curr, recommendations: formatted },
              null,
              2
            ),
          },
        ],
      };
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      return {
        content: [{ type: "text", text: `Error recommending models: ${message}` }],
        isError: true,
      };
    }
  }
);

// Tool 6: estimate_monthly_cost
server.registerTool(
  "estimate_monthly_cost",
  {
    description:
      "Estimate daily, monthly, and annual AI API costs for a recurring production workload.",
    inputSchema: {
      model_id: z.string().describe("Model ID or alias (e.g., 'gpt-6.2-sol', 'claude-sonnet-5.5')"),
      requests_per_day: z.number().describe("Average requests per day"),
      avg_input_tokens: z
        .number()
        .int()
        .optional()
        .describe("Average uncached input tokens per request"),
      avg_cached_input_tokens: z
        .number()
        .int()
        .optional()
        .describe("Average cached input tokens per request"),
      avg_output_tokens: z
        .number()
        .int()
        .optional()
        .describe("Average output tokens per request"),
      avg_units: z
        .number()
        .optional()
        .describe("Average units per request (for non-text models)"),
      days: z.number().int().optional().describe("Days in billing cycle (default: 30)"),
      batch: z.boolean().optional().describe("Whether requests use Batch API (default: false)"),
      currency: z.string().optional().describe("Target currency code (default: 'USD')"),
    },
  },
  async ({
    model_id,
    requests_per_day,
    avg_input_tokens,
    avg_cached_input_tokens,
    avg_output_tokens,
    avg_units,
    days,
    batch,
    currency,
  }) => {
    try {
      const { model: found, suggestions } = await resolveModelWithLiveFallback(model_id);
      if (!found) {
        const hint = suggestions.length > 0 ? ` Did you mean: ${suggestions.join(", ")}?` : "";
        return {
          content: [{ type: "text", text: `Error: Model '${model_id}' not found.${hint}` }],
          isError: true,
        };
      }

      const est = estimateMonthlyCost(found, {
        requestsPerDay: requests_per_day,
        avgInputTokens: avg_input_tokens,
        avgCachedInputTokens: avg_cached_input_tokens,
        avgOutputTokens: avg_output_tokens,
        avgUnits: avg_units,
        days,
        batch,
      });
      const { rate, currency: curr } = await getExchangeRate(currency);

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(
              {
                model_id: est.model_id,
                provider: est.provider,
                currency: curr,
                requests_per_day: est.requests_per_day,
                days: est.days,
                per_request_cost: roundNum(est.per_request_usd * rate, 6),
                daily_cost: roundNum(est.daily_usd * rate, 4),
                period_base_cost: roundNum(est.period_base_usd * rate, 4),
                period_fee_cost: roundNum(est.period_fee_usd * rate, 4),
                period_total_cost: roundNum(est.period_total_usd * rate, 4),
                annual_total_cost: roundNum(est.annual_total_usd * rate, 2),
                period_requests: est.period_requests,
                period_input_tokens: est.period_input_tokens,
                period_output_tokens: est.period_output_tokens,
              },
              null,
              2
            ),
          },
        ],
      };
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      return {
        content: [{ type: "text", text: `Error estimating budget: ${message}` }],
        isError: true,
      };
    }
  }
);

// Tool 7: get_pricing_metadata
server.registerTool(
  "get_pricing_metadata",
  {
    description:
      "Get metadata about the current pricing database (schema version, model count, live catalog count, last update date, currency cache timestamp).",
    inputSchema: {},
  },
  async () => {
    const meta = await getPricingMetadata();
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(
            {
              ...meta,
              currency_cached_at: getCurrencyDate(),
              server_version: SERVER_VERSION,
            },
            null,
            2
          ),
        },
      ],
    };
  }
);

// Tool 8: sync_pricing_data
server.registerTool(
  "sync_pricing_data",
  {
    description:
      "Fetch the latest curated pricing database, refresh 400+ live OpenRouter models, and update currency exchange rates.",
    inputSchema: {},
  },
  async () => {
    const [remote, liveModels, rates] = await Promise.all([
      fetchRemotePricing(),
      fetchLiveCatalog(),
      refreshRates(),
    ]);
    const fallbackMeta = await getPricingMetadata();
    const synced = Boolean(remote) || liveModels.length > 0;
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(
            {
              pricing_synced: Boolean(remote),
              last_updated: remote?.last_updated ?? fallbackMeta.last_updated,
              live_catalog_synced: liveModels.length > 0,
              live_catalog_count: liveModels.length,
              currencies_synced: Object.keys(rates).length > 1,
              currency_count: Object.keys(rates).length,
            },
            null,
            2
          ),
        },
      ],
      isError: !synced,
    };
  }
);

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error(`aicost-mcp v${SERVER_VERSION} running on stdio`);
}

main().catch((error) => {
  console.error("Fatal error running aicost-mcp:", error);
  process.exit(1);
});
