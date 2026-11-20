import fs from "node:fs";
import path from "node:path";
import { CACHE_DIR } from "./data.js";

const EXCHANGE_CACHE_FILE = path.join(CACHE_DIR, "exchange_cache.json");
const LEGACY_CACHE_FILE = path.join(CACHE_DIR, "currency_cache.json");
const CACHE_TTL_SEC = 24 * 60 * 60; // 24 hours

const PRIMARY_CURRENCY_URL =
  "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.min.json";
const FALLBACK_CDN_URL =
  "https://latest.currency-api.pages.dev/v1/currencies/usd.min.json";
const FALLBACK_ECB_URL = "https://api.frankfurter.app/latest?from=USD";

interface CachedExchangePayload {
  timestamp?: number;
  api_date?: string;
  rates?: Record<string, number>;
}

function normalizeRates(raw: Record<string, unknown> | undefined): Record<string, number> {
  const normalized: Record<string, number> = { USD: 1.0 };
  if (!raw) return normalized;
  for (const [code, value] of Object.entries(raw)) {
    const num = Number(value);
    if (Number.isFinite(num) && num > 0) {
      normalized[code.toUpperCase()] = num;
    }
  }
  return normalized;
}

function loadCachedExchange(): CachedExchangePayload | null {
  for (const filePath of [EXCHANGE_CACHE_FILE, LEGACY_CACHE_FILE]) {
    try {
      if (!fs.existsSync(filePath)) continue;
      const parsed = JSON.parse(fs.readFileSync(filePath, "utf-8")) as CachedExchangePayload;
      if (parsed && parsed.rates && typeof parsed.rates === "object") {
        return parsed;
      }
    } catch {
      // Ignore corrupt cache
    }
  }
  return null;
}

function saveCachedExchange(rates: Record<string, number>, apiDate: string): void {
  try {
    fs.mkdirSync(CACHE_DIR, { recursive: true });
    const payload: CachedExchangePayload = {
      timestamp: Date.now() / 1000,
      api_date: apiDate,
      rates,
    };
    fs.writeFileSync(EXCHANGE_CACHE_FILE, JSON.stringify(payload), "utf-8");
  } catch {
    // Non-fatal if filesystem is read-only
  }
}

async function fetchFromApis(): Promise<{ rates: Record<string, number>; apiDate: string }> {
  for (const url of [PRIMARY_CURRENCY_URL, FALLBACK_CDN_URL]) {
    try {
      const res = await fetch(url, { signal: AbortSignal.timeout(5_000) });
      if (!res.ok) continue;
      const payload = (await res.json()) as { date?: string; usd?: Record<string, unknown> };
      const rates = normalizeRates(payload.usd);
      if (Object.keys(rates).length > 1) {
        return { rates, apiDate: String(payload.date ?? "") };
      }
    } catch {
      // Try next mirror
    }
  }

  try {
    const res = await fetch(FALLBACK_ECB_URL, { signal: AbortSignal.timeout(5_000) });
    if (res.ok) {
      const payload = (await res.json()) as { date?: string; rates?: Record<string, unknown> };
      const rates = normalizeRates(payload.rates);
      if (Object.keys(rates).length > 1) {
        return { rates, apiDate: String(payload.date ?? "") };
      }
    }
  } catch {
    // Fallback exhausted
  }

  return { rates: { USD: 1.0 }, apiDate: "" };
}

export async function refreshRates(): Promise<Record<string, number>> {
  const { rates, apiDate } = await fetchFromApis();
  if (Object.keys(rates).length > 1) {
    saveCachedExchange(rates, apiDate);
  }
  return rates;
}

export async function getRates(): Promise<Record<string, number>> {
  const nowSec = Date.now() / 1000;
  const cached = loadCachedExchange();
  let staleRates: Record<string, number> | null = null;

  if (cached?.rates) {
    staleRates = normalizeRates(cached.rates);
    if (Object.keys(staleRates).length > 1 && nowSec - (cached.timestamp ?? 0) < CACHE_TTL_SEC) {
      return staleRates;
    }
  }

  const { rates, apiDate } = await fetchFromApis();
  if (Object.keys(rates).length > 1) {
    saveCachedExchange(rates, apiDate);
    return rates;
  }

  if (staleRates && Object.keys(staleRates).length > 1) {
    console.error("Warning: Could not refresh exchange rates. Using cached rates.");
    return staleRates;
  }

  return { USD: 1.0 };
}

export async function getExchangeRate(
  toCurrency?: string
): Promise<{ rate: number; currency: string }> {
  const target = (toCurrency ?? "USD").trim().toUpperCase() || "USD";
  if (target === "USD") {
    return { rate: 1.0, currency: "USD" };
  }

  const rates = await getRates();
  if (target in rates) {
    return { rate: rates[target], currency: target };
  }

  console.error(
    `Warning: Currency '${target}' not found or network unavailable. Falling back to USD.`
  );
  return { rate: 1.0, currency: "USD" };
}

export function getCurrencyDate(): string {
  const cached = loadCachedExchange();
  if (cached?.timestamp) {
    return new Date(cached.timestamp * 1000).toISOString().replace("T", " ").slice(0, 19);
  }
  if (cached?.api_date) {
    return cached.api_date;
  }
  return "Live / No Cache";
}
