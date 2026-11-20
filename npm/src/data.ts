import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { ModelEntry, PricingDatabase } from "./types.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export const CACHE_DIR = path.join(os.homedir(), ".aicost");
export const PRICING_CACHE_FILE = path.join(CACHE_DIR, "pricing_cache.json");
const CACHE_TTL_MS = 7 * 24 * 60 * 60 * 1000; // 7 days
export const REMOTE_PRICING_URL =
  "https://raw.githubusercontent.com/ufhouck/aicost/main/data/pricing.json";

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
    path.resolve(__dirname, "..", "data", "pricing.json"),       // npm packaged data/pricing.json
    path.resolve(__dirname, "..", "..", "data", "pricing.json"), // monorepo root data/pricing.json
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

export async function getAllPricingData(): Promise<PricingDatabase> {
  const bundled = loadBundledPricing();
  const cached = loadCachedPricing();

  if (cached && bundled) {
    if ((cached.last_updated ?? "") >= (bundled.last_updated ?? "")) {
      return cached;
    }
    return bundled;
  }
  if (cached) return cached;
  if (bundled) return bundled;

  const remote = await fetchRemotePricing();
  return remote ?? { schema_version: "2.0", last_updated: "Unknown", models: [] };
}

export async function getPricingModels(): Promise<ModelEntry[]> {
  const db = await getAllPricingData();
  return db.models;
}

export async function getPricingMetadata(): Promise<{
  schema_version: string;
  last_updated: string;
  model_count: number;
}> {
  const db = await getAllPricingData();
  return {
    schema_version: db.schema_version ?? "2.0",
    last_updated: db.last_updated ?? "Unknown",
    model_count: db.models.length,
  };
}
