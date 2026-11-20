import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { ModelEntry, PricingDatabase } from "./types.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export const CACHE_DIR = path.join(os.homedir(), ".aicost");
export const PRICING_CACHE_FILE = path.join(CACHE_DIR, "pricing_cache.json");
export const LIVE_CATALOG_CACHE_FILE = path.join(CACHE_DIR, "live_catalog_cache.json");

const CACHE_TTL_MS = 7 * 24 * 60 * 60 * 1000; // 7 days
const LIVE_CACHE_TTL_MS = 24 * 60 * 60 * 1000; // 24 hours

export const REMOTE_PRICING_URL =
  "https://raw.githubusercontent.com/ufhouck/aicost/main/data/pricing.json";
export const OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models";

const PROVIDER_DISPLAY_NAMES: Record<string, string> = {
  openai: "OpenAI",
  anthropic: "Anthropic",
  google: "Google",
  "x-ai": "xAI",
  deepseek: "DeepSeek",
  qwen: "Alibaba Qwen",
  "meta-llama": "Meta",
  mistralai: "Mistral",
  moonshotai: "Moonshot",
  minimax: "MiniMax",
  perplexity: "Perplexity",
  amazon: "Amazon",
  cohere: "Cohere",
  nvidia: "NVIDIA",
  microsoft: "Microsoft",
  ai21: "AI21",
  "black-forest-labs": "Black Forest Labs",
};

function readJsonIfValid(filePath: string): PricingDatabase | null {
  try {
    if (!fs.existsSync(filePath)) return null;
    const raw = fs.readFileSync(filePath, "utf-8");
    const parsed = JSON.parse(raw) as PricingDatabase;
    if (parsed && Array.isArray(parsed.models)) {
      return parsed;
    }
  } catch {
    // Ignore malformed cache/file
  }
  return null;
}

function loadBundledPricing(): PricingDatabase | null {
  const candidates = [
    path.resolve(__dirname, "..", "data", "pricing.json"),
    path.resolve(__dirname, "..", "..", "data", "pricing.json"),
  ];

  for (const candidate of candidates) {
    const data = readJsonIfValid(candidate);
    if (data) return data;
  }
  return null;
}

function loadCachedPricing(): PricingDatabase | null {
  try {
    if (!fs.existsSync(PRICING_CACHE_FILE)) return null;
    const stats = fs.statSync(PRICING_CACHE_FILE);
    if (Date.now() - stats.mtimeMs > CACHE_TTL_MS) return null;
    return readJsonIfValid(PRICING_CACHE_FILE);
  } catch {
    return null;
  }
}

export async function fetchRemotePricing(): Promise<PricingDatabase | null> {
  try {
    const response = await fetch(REMOTE_PRICING_URL, {
      signal: AbortSignal.timeout(10_000),
    });
    if (!response.ok) return null;
    const data = (await response.json()) as PricingDatabase;
    if (!data || !Array.isArray(data.models)) return null;

    fs.mkdirSync(CACHE_DIR, { recursive: true });
    fs.writeFileSync(PRICING_CACHE_FILE, JSON.stringify(data, null, 2), "utf-8");
    return data;
  } catch {
    return null;
  }
}

interface RawOpenRouterModel {
  id?: string;
  name?: string;
  context_length?: number;
  architecture?: { input_modalities?: string[] };
  pricing?: {
    prompt?: string | number;
    completion?: string | number;
    input_cache_read?: string | number;
  };
}

function convertOpenRouterEntry(rm: RawOpenRouterModel): ModelEntry | null {
  const orId = String(rm.id ?? "").trim();
  if (!orId || orId.includes(":free") || orId.includes(":batch")) {
    return null;
  }

  const inCost = Number(rm.pricing?.prompt ?? 0) * 1_000_000;
  const outCost = Number(rm.pricing?.completion ?? 0) * 1_000_000;
  if (!Number.isFinite(inCost) || !Number.isFinite(outCost) || (inCost <= 0 && outCost <= 0)) {
    return null;
  }

  const [rawPrefix, rawShort] = orId.includes("/") ? orId.split("/", 2) : ["openrouter", orId];
  const prefix = rawPrefix.toLowerCase();
  const provider =
    PROVIDER_DISPLAY_NAMES[prefix] ??
    prefix
      .split("-")
      .map((s) => s.charAt(0).toUpperCase() + s.slice(1))
      .join(" ");

  const inMods = (rm.architecture?.input_modalities ?? []).map((x) => String(x).toLowerCase());
  const ctx = Number(rm.context_length ?? 0);

  const tags = ["live-catalog"];
  if (inMods.includes("image")) tags.push("vision", "multimodal");
  if (ctx >= 500_000) tags.push("long-context");
  if (inCost <= 0.35) tags.push("cheap", "fast");

  const entry: ModelEntry = {
    id: orId,
    aliases: [rawShort],
    openrouter_id: orId.toLowerCase(),
    provider,
    source_type: "direct",
    type: "text",
    billing_unit: "1m_tokens",
    context_window: ctx > 0 ? ctx : undefined,
    cost_per_1m_input_tokens: Math.round(inCost * 10000) / 10000,
    cost_per_1m_output_tokens: Math.round(outCost * 10000) / 10000,
    tags,
    description: String(rm.name ?? orId),
  };

  if (rm.pricing?.input_cache_read !== undefined && rm.pricing.input_cache_read !== null) {
    const cacheCost = Math.round(Number(rm.pricing.input_cache_read) * 1_000_000 * 10000) / 10000;
    if (Number.isFinite(cacheCost) && cacheCost > 0) {
      entry.cost_per_1m_cached_input_tokens = cacheCost;
    }
  }

  return entry;
}

export async function fetchLiveCatalog(): Promise<ModelEntry[]> {
  try {
    const response = await fetch(OPENROUTER_MODELS_URL, {
      signal: AbortSignal.timeout(8_000),
    });
    if (!response.ok) return [];
    const payload = (await response.json()) as { data?: RawOpenRouterModel[] };
    if (!Array.isArray(payload.data)) return [];

    const converted: ModelEntry[] = [];
    for (const rm of payload.data) {
      const item = convertOpenRouterEntry(rm);
      if (item) converted.push(item);
    }

    if (converted.length > 0) {
      fs.mkdirSync(CACHE_DIR, { recursive: true });
      fs.writeFileSync(
        LIVE_CATALOG_CACHE_FILE,
        JSON.stringify({ timestamp: Date.now() / 1000, models: converted }),
        "utf-8"
      );
    }
    return converted;
  } catch {
    return [];
  }
}

export async function getLiveCatalog(autoFetch = true): Promise<ModelEntry[]> {
  let stale: ModelEntry[] = [];
  try {
    if (fs.existsSync(LIVE_CATALOG_CACHE_FILE)) {
      const parsed = JSON.parse(fs.readFileSync(LIVE_CATALOG_CACHE_FILE, "utf-8")) as {
        timestamp?: number;
        models?: ModelEntry[];
      };
      if (Array.isArray(parsed.models)) {
        stale = parsed.models;
        if (stale.length > 0 && Date.now() - Number(parsed.timestamp ?? 0) * 1000 < LIVE_CACHE_TTL_MS) {
          return stale;
        }
      }
    }
  } catch {
    // Ignore malformed cache
  }

  if (autoFetch) {
    const fresh = await fetchLiveCatalog();
    if (fresh.length > 0) return fresh;
  }

  return stale;
}

export async function getAllPricingData(): Promise<PricingDatabase> {
  const bundled = loadBundledPricing();
  const cached = loadCachedPricing();

  if (cached && bundled) {
    const cachedDate = cached.last_updated ?? "";
    const bundledDate = bundled.last_updated ?? "";
    if (
      cachedDate > bundledDate ||
      (cachedDate === bundledDate && cached.models.length >= bundled.models.length)
    ) {
      return cached;
    }
    return bundled;
  }
  if (cached) return cached;
  if (bundled) return bundled;

  const remote = await fetchRemotePricing();
  return remote ?? { schema_version: "2.1", last_updated: "Unknown", models: [] };
}

export async function getPricingModels(includeLive = false): Promise<ModelEntry[]> {
  const db = await getAllPricingData();
  if (!includeLive) return db.models;

  const known = new Set<string>();
  for (const m of db.models) {
    known.add(m.id.toLowerCase());
    if (m.openrouter_id) known.add(m.openrouter_id.toLowerCase());
  }

  const merged = [...db.models];
  const live = await getLiveCatalog(true);
  for (const lm of live) {
    const lid = lm.id.toLowerCase();
    if (!known.has(lid)) {
      merged.push(lm);
      known.add(lid);
    }
  }
  return merged;
}

export async function getPricingMetadata(): Promise<{
  schema_version: string;
  last_updated: string;
  model_count: number;
  live_catalog_cached_count: number;
}> {
  const db = await getAllPricingData();
  const liveCached = await getLiveCatalog(false);
  return {
    schema_version: db.schema_version ?? "2.1",
    last_updated: db.last_updated ?? "Unknown",
    model_count: db.models.length,
    live_catalog_cached_count: liveCached.length,
  };
}
