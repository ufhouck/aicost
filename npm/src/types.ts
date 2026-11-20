export type ModelType = "text" | "image" | "video" | "audio" | "gateway";
export type SourceType = "direct" | "aggregator" | "gateway";
export type BillingUnit =
  | "1m_tokens"
  | "image"
  | "second"
  | "minute"
  | "song"
  | "clip"
  | "1m_chars"
  | "month"
  | "custom"
  | "unit";

export interface ModelEntry {
  id: string;
  aliases?: string[];
  openrouter_id?: string;
  provider: string;
  source_type?: SourceType;
  platform_fee?: number;
  type?: ModelType;
  billing_unit?: BillingUnit;
  context_window?: number;
  cost_per_1m_input_tokens?: number;
  cost_per_1m_cached_input_tokens?: number;
  cost_per_1m_output_tokens?: number;
  cost_per_unit?: number;
  fixed_monthly_cost?: number;
  batch_discount?: number;
  tags?: string[];
  description?: string;
}

export interface PricingDatabase {
  schema_version?: string;
  last_updated: string;
  models: ModelEntry[];
}

export interface EffectiveRates {
  platform_fee: number;
  input_per_1m: number | null;
  cached_input_per_1m: number | null;
  output_per_1m: number | null;
  per_unit: number | null;
  monthly: number | null;
}

export interface CostBreakdown {
  model_id: string;
  provider: string;
  source_type: string;
  model_type: string;
  billing_unit: string;
  unit_label: string;
  is_custom_pricing: boolean;
  usage_summary: string;
  raw_base_usd: number;
  batch_applied: boolean;
  batch_discount_rate: number;
  batch_savings_usd: number;
  base_usd: number;
  platform_fee_rate: number;
  platform_fee_usd: number;
  total_usd: number;
}

export interface MonthlyEstimate {
  model_id: string;
  provider: string;
  source_type: string;
  model_type: string;
  is_custom_pricing: boolean;
  batch_applied: boolean;
  platform_fee_rate: number;
  requests_per_day: number;
  days: number;
  per_request_usd: number;
  daily_usd: number;
  period_base_usd: number;
  period_fee_usd: number;
  period_total_usd: number;
  annual_total_usd: number;
  period_requests: number;
  period_input_tokens: number;
  period_cached_input_tokens: number;
  period_output_tokens: number;
}
