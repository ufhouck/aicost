import type { CostBreakdown, EffectiveRates, ModelEntry, MonthlyEstimate } from "./types.js";

const UNIT_LABELS: Record<string, string> = {
  "1m_tokens": "1M tokens",
  image: "image",
  second: "sec",
  minute: "min",
  song: "song",
  clip: "clip",
  "1m_chars": "1M chars",
  month: "mo",
  custom: "custom",
};

const GATEWAY_KEYWORDS = new Set([
  "gateway",
  "proxy",
  "governance",
  "observability",
  "sso",
  "audit",
  "audit-logs",
  "router",
]);

export function formatUnitLabel(billingUnit?: string, modelType = "text"): string {
  if (billingUnit && billingUnit in UNIT_LABELS) {
    return UNIT_LABELS[billingUnit];
  }
  if (modelType === "text") return "1M tokens";
  if (modelType === "gateway") return "mo";
  return "unit";
}

export function getEffectiveRates(model: ModelEntry): EffectiveRates {
  const fee = Number(model.platform_fee ?? 0);
  const multiplier = 1 + fee;

  return {
    platform_fee: fee,
    input_per_1m:
      model.cost_per_1m_input_tokens !== undefined
        ? model.cost_per_1m_input_tokens * multiplier
        : null,
    cached_input_per_1m:
      model.cost_per_1m_cached_input_tokens !== undefined
        ? model.cost_per_1m_cached_input_tokens * multiplier
        : null,
    output_per_1m:
      model.cost_per_1m_output_tokens !== undefined
        ? model.cost_per_1m_output_tokens * multiplier
        : null,
    per_unit: model.cost_per_unit !== undefined ? model.cost_per_unit * multiplier : null,
    monthly: model.fixed_monthly_cost !== undefined ? model.fixed_monthly_cost : null,
  };
}

function effectiveSortCost(model: ModelEntry): number {
  const eff = getEffectiveRates(model);
  for (const val of [eff.input_per_1m, eff.per_unit, eff.monthly]) {
    if (val !== null) return val;
  }
  return Number.POSITIVE_INFINITY;
}

export function filterModels(
  models: ModelEntry[],
  options: {
    provider?: string;
    modelType?: string;
    tag?: string;
    includeLegacy?: boolean;
  }
): ModelEntry[] {
  const includeLegacy = options.includeLegacy ?? true;
  const prov = options.provider?.trim().toLowerCase();
  const mType = options.modelType?.trim().toLowerCase();
  const tagFilter = options.tag?.trim().toLowerCase();

  return models
    .filter((m) => {
      const tags = (m.tags ?? []).map((t) => t.toLowerCase());
      if (!includeLegacy && tags.includes("legacy")) return false;
      if (prov && m.provider.toLowerCase() !== prov) return false;
      if (mType && (m.type ?? "text").toLowerCase() !== mType) return false;
      if (tagFilter && !tags.includes(tagFilter)) return false;
      return true;
    })
    .sort((a, b) => effectiveSortCost(a) - effectiveSortCost(b));
}

function matchInList(models: ModelEntry[], query: string): ModelEntry | undefined {
  const exact = models.find((m) => m.id.toLowerCase() === query);
  if (exact) return exact;

  const byOrId = models.find((m) => (m.openrouter_id ?? "").toLowerCase() === query);
  if (byOrId) return byOrId;

  return models.find((m) => (m.aliases ?? []).some((a) => a.toLowerCase() === query));
}

export function synthesizeOpenRouterAggregator(
  baseModel: ModelEntry,
  requestedId: string
): ModelEntry {
  const cleanSuffix = requestedId.replace(/^openrouter\//i, "");
  const tags = (baseModel.tags ?? []).filter((t) => t !== "direct");
  if (!tags.includes("aggregator")) tags.unshift("aggregator");
  const { batch_discount: _unused, ...rest } = baseModel;
  return {
    ...rest,
    id: `openrouter/${cleanSuffix}`,
    provider: "OpenRouter",
    source_type: "aggregator",
    platform_fee: 0.055,
    tags,
    description: `${baseModel.id} via OpenRouter aggregator (+5.5% platform fee).`,
  };
}

export function findModelById(
  models: ModelEntry[],
  modelId: string,
  liveModels: ModelEntry[] = []
): ModelEntry | undefined {
  const query = modelId.trim().toLowerCase();
  if (!query) return undefined;

  const curatedHit = matchInList(models, query);
  if (curatedHit) return curatedHit;

  if (query.startsWith("openrouter/")) {
    const subQuery = query.slice("openrouter/".length);
    const curatedBase = matchInList(models, subQuery);
    if (curatedBase && (curatedBase.type ?? "text") === "text") {
      return synthesizeOpenRouterAggregator(curatedBase, query);
    }
    const liveBase = matchInList(liveModels, subQuery);
    if (liveBase) {
      return synthesizeOpenRouterAggregator(liveBase, query);
    }
  }

  return matchInList(liveModels, query);
}

function diceSimilarity(a: string, b: string): number {
  if (a === b) return 1;
  if (a.length < 2 || b.length < 2) return 0;
  const bigrams = new Map<string, number>();
  for (let i = 0; i < a.length - 1; i++) {
    const bg = a.slice(i, i + 2);
    bigrams.set(bg, (bigrams.get(bg) ?? 0) + 1);
  }
  let matches = 0;
  for (let i = 0; i < b.length - 1; i++) {
    const bg = b.slice(i, i + 2);
    const count = bigrams.get(bg) ?? 0;
    if (count > 0) {
      bigrams.set(bg, count - 1);
      matches++;
    }
  }
  return (2 * matches) / (a.length + b.length - 2);
}

export function suggestSimilarModels(models: ModelEntry[], query: string, limit = 3): string[] {
  const q = query.trim().toLowerCase();
  if (!q) return [];

  const scored = models
    .map((m) => {
      const idLower = m.id.toLowerCase();
      const subBonus = idLower.includes(q) || q.includes(idLower) ? 0.5 : 0;
      const sim = diceSimilarity(q, idLower) + subBonus;
      return { id: m.id, sim };
    })
    .filter((x) => x.sim >= 0.35)
    .sort((a, b) => b.sim - a.sim);

  return scored.slice(0, limit).map((x) => x.id);
}

export function calculateCostBreakdown(
  model: ModelEntry,
  options: {
    inputTokens?: number;
    outputTokens?: number;
    cachedInputTokens?: number;
    units?: number;
    batch?: boolean;
  }
): CostBreakdown {
  const mType = model.type ?? "text";
  const billingUnit = model.billing_unit ?? (mType === "text" ? "1m_tokens" : "unit");
  const unitLabel = formatUnitLabel(billingUnit, mType);
  const feeRate = Number(model.platform_fee ?? 0);

  let isCustomPricing = false;
  let rawBaseUsd = 0;
  let batchApplied = false;
  let batchDiscountRate = 0;
  let batchSavingsUsd = 0;
  let usageSummary = "";

  const inTokens = Math.max(0, Math.trunc(options.inputTokens ?? 0));
  const cachedTokens = Math.max(0, Math.trunc(options.cachedInputTokens ?? 0));
  const outTokens = Math.max(0, Math.trunc(options.outputTokens ?? 0));
  const units = Math.max(0, Number(options.units ?? 0));

  if (mType === "text") {
    const inRate = Number(model.cost_per_1m_input_tokens ?? 0);
    const cachedRate = Number(model.cost_per_1m_cached_input_tokens ?? inRate);
    const outRate = Number(model.cost_per_1m_output_tokens ?? 0);

    rawBaseUsd =
      (inTokens / 1_000_000) * inRate +
      (cachedTokens / 1_000_000) * cachedRate +
      (outTokens / 1_000_000) * outRate;

    if (options.batch && Number(model.batch_discount ?? 0) > 0) {
      batchApplied = true;
      batchDiscountRate = Number(model.batch_discount);
      batchSavingsUsd = rawBaseUsd * batchDiscountRate;
    }

    const parts = [`${inTokens.toLocaleString("en-US")} in`];
    if (cachedTokens > 0) {
      parts.push(`${cachedTokens.toLocaleString("en-US")} cached-in`);
    }
    parts.push(`${outTokens.toLocaleString("en-US")} out`);
    usageSummary = `Text (${parts.join(", ")})`;
    if (batchApplied) {
      usageSummary += ` [Batch -${Math.round(batchDiscountRate * 100)}%]`;
    }
  } else if (mType === "gateway") {
    const effectiveMonths = units > 0 ? units : 1;
    if (model.fixed_monthly_cost === undefined) {
      isCustomPricing = true;
      rawBaseUsd = 0;
      usageSummary = "Gateway (Custom enterprise pricing)";
    } else {
      rawBaseUsd = effectiveMonths * model.fixed_monthly_cost;
      usageSummary = `Gateway (${effectiveMonths} ${unitLabel})`;
    }
  } else {
    const unitRate = Number(model.cost_per_unit ?? 0);
    rawBaseUsd = units * unitRate;
    if (options.batch && Number(model.batch_discount ?? 0) > 0) {
      batchApplied = true;
      batchDiscountRate = Number(model.batch_discount);
      batchSavingsUsd = rawBaseUsd * batchDiscountRate;
    }
    const capType = mType.charAt(0).toUpperCase() + mType.slice(1);
    usageSummary = `${capType}: ${units} ${unitLabel}`;
    if (batchApplied) {
      usageSummary += ` [Batch -${Math.round(batchDiscountRate * 100)}%]`;
    }
  }

  const baseUsd = rawBaseUsd - batchSavingsUsd;
  const platformFeeUsd = baseUsd * feeRate;
  const totalUsd = baseUsd + platformFeeUsd;

  return {
    model_id: model.id,
    provider: model.provider,
    source_type: model.source_type ?? "direct",
    model_type: mType,
    billing_unit: billingUnit,
    unit_label: unitLabel,
    is_custom_pricing: isCustomPricing,
    usage_summary: usageSummary,
    raw_base_usd: rawBaseUsd,
    batch_applied: batchApplied,
    batch_discount_rate: batchDiscountRate,
    batch_savings_usd: batchSavingsUsd,
    base_usd: baseUsd,
    platform_fee_rate: feeRate,
    platform_fee_usd: platformFeeUsd,
    total_usd: totalUsd,
  };
}

export function estimateMonthlyCost(
  model: ModelEntry,
  options: {
    requestsPerDay: number;
    avgInputTokens?: number;
    avgOutputTokens?: number;
    avgCachedInputTokens?: number;
    avgUnits?: number;
    days?: number;
    batch?: boolean;
  }
): MonthlyEstimate {
  const rpd = Math.max(0, Number(options.requestsPerDay));
  const periodDays = Math.max(1, Math.trunc(options.days ?? 30));
  const mType = model.type ?? "text";

  if (mType === "gateway") {
    const monthlyFixed = Number(model.fixed_monthly_cost ?? 0);
    const isCustom = model.fixed_monthly_cost === undefined;
    const dailyUsd = monthlyFixed / 30;
    const periodUsd = dailyUsd * periodDays;
    return {
      model_id: model.id,
      provider: model.provider,
      source_type: model.source_type ?? "gateway",
      model_type: "gateway",
      is_custom_pricing: isCustom,
      batch_applied: false,
      platform_fee_rate: 0,
      requests_per_day: rpd,
      days: periodDays,
      per_request_usd: rpd > 0 ? dailyUsd / rpd : 0,
      daily_usd: dailyUsd,
      period_base_usd: periodUsd,
      period_fee_usd: 0,
      period_total_usd: periodUsd,
      annual_total_usd: monthlyFixed * 12,
      period_requests: rpd * periodDays,
      period_input_tokens: 0,
      period_cached_input_tokens: 0,
      period_output_tokens: 0,
    };
  }

  const perReq = calculateCostBreakdown(model, {
    inputTokens: options.avgInputTokens ?? 0,
    outputTokens: options.avgOutputTokens ?? 0,
    cachedInputTokens: options.avgCachedInputTokens ?? 0,
    units: options.avgUnits && options.avgUnits > 0 ? options.avgUnits : 1,
    batch: options.batch ?? false,
  });

  const dailyBase = perReq.base_usd * rpd;
  const dailyFee = perReq.platform_fee_usd * rpd;
  const dailyTotal = perReq.total_usd * rpd;

  return {
    model_id: model.id,
    provider: model.provider,
    source_type: model.source_type ?? "direct",
    model_type: mType,
    is_custom_pricing: perReq.is_custom_pricing,
    batch_applied: perReq.batch_applied,
    platform_fee_rate: perReq.platform_fee_rate,
    requests_per_day: rpd,
    days: periodDays,
    per_request_usd: perReq.total_usd,
    daily_usd: dailyTotal,
    period_base_usd: dailyBase * periodDays,
    period_fee_usd: dailyFee * periodDays,
    period_total_usd: dailyTotal * periodDays,
    annual_total_usd: dailyTotal * 365,
    period_requests: rpd * periodDays,
    period_input_tokens: Math.trunc(rpd * periodDays * Math.max(0, options.avgInputTokens ?? 0)),
    period_cached_input_tokens: Math.trunc(
      rpd * periodDays * Math.max(0, options.avgCachedInputTokens ?? 0)
    ),
    period_output_tokens: Math.trunc(rpd * periodDays * Math.max(0, options.avgOutputTokens ?? 0)),
  };
}

export function recommendModels(
  models: ModelEntry[],
  options: {
    taskDescription: string;
    limit?: number;
    modelType?: string;
    maxInputCost?: number;
    includeLegacy?: boolean;
  }
): ModelEntry[] {
  const rawTask = options.taskDescription.trim().toLowerCase();
  if (!rawTask) return [];

  const words = new Set(
    rawTask
      .replace(/[,./]/g, " ")
      .split(/\s+/)
      .map((w) => w.trim())
      .filter(Boolean)
  );

  const wantsLegacy = Boolean(options.includeLegacy) || words.has("legacy");
  const wantsGateway =
    [...words].some((w) => GATEWAY_KEYWORDS.has(w)) ||
    options.modelType?.toLowerCase() === "gateway";

  const scored: Array<{ score: number; cost: number; model: ModelEntry }> = [];

  for (const model of models) {
    const mType = (model.type ?? "text").toLowerCase();
    const tags = (model.tags ?? []).map((t) => t.toLowerCase());
    const desc = (model.description ?? "").toLowerCase();

    if (!wantsLegacy && tags.includes("legacy")) continue;
    if (mType === "gateway" && !wantsGateway) continue;
    if (options.modelType && mType !== options.modelType.trim().toLowerCase()) continue;

    if (options.maxInputCost !== undefined) {
      const eff = getEffectiveRates(model);
      const refCost = eff.input_per_1m ?? eff.per_unit;
      if (refCost === null || refCost > options.maxInputCost) continue;
    }

    let score = 0;
    for (const word of words) {
      if (tags.includes(word)) {
        score += 3;
      } else if (word === mType || word === model.provider.toLowerCase()) {
        score += 2;
      } else if (word.length > 2 && desc.includes(word)) {
        score += 1;
      }
    }

    if (score > 0) {
      if ((words.has("cheap") || words.has("budget") || rawTask.includes("low-cost")) && tags.includes("cheap")) {
        score += 5;
      }
      if (words.has("fast") && tags.includes("fast")) {
        score += 2;
      }
      if ((rawTask.includes("agent") || words.has("agentic")) && tags.includes("agentic")) {
        score += 4;
      }
      if (
        (words.has("vision") || words.has("image") || words.has("ocr")) &&
        (tags.includes("vision") || tags.includes("image") || tags.includes("ocr"))
      ) {
        score += 4;
      }

      scored.push({ score, cost: effectiveSortCost(model), model });
    }
  }

  scored.sort((a, b) => (b.score !== a.score ? b.score - a.score : a.cost - b.cost));
  return scored.slice(0, Math.max(1, options.limit ?? 3)).map((s) => s.model);
}
