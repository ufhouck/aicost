from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from aicost import __version__
from aicost.calculator import (
    calculate_cost_breakdown,
    calculate_image_cost,
    calculate_text_cost,
    estimate_monthly_cost,
    filter_models,
    get_all_data,
    get_model_by_id,
    get_pricing_data,
    suggest_similar_models,
)
from aicost.cli import app
from aicost.mcp_server import execute_mcp_tool, read_mcp_resource
from aicost.recommender import recommend_models

runner = CliRunner()


def test_pricing_json_schema_integrity() -> None:
    repo_json = Path(__file__).resolve().parent.parent / "data" / "pricing.json"
    assert repo_json.exists(), "Root data/pricing.json must exist"

    with open(repo_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "last_updated" in data
    models = data.get("models", [])
    assert len(models) >= 29

    seen_ids: set[str] = set()
    valid_types = {"text", "image", "video", "audio", "gateway"}
    valid_units = {"1m_tokens", "image", "second", "minute", "song", "clip", "1m_chars", "month", "custom"}

    for m in models:
        mid = m["id"]
        assert mid not in seen_ids, f"Duplicate model ID: {mid}"
        seen_ids.add(mid)
        assert m.get("type") in valid_types
        assert m.get("billing_unit") in valid_units
        assert m.get("provider")
        assert isinstance(m.get("tags"), list) and len(m["tags"]) > 0

        if m["type"] == "text":
            assert m["cost_per_1m_input_tokens"] > 0
            assert m["cost_per_1m_output_tokens"] > 0
            if "openrouter_id" in m:
                assert "/" in m["openrouter_id"]
        elif m["type"] in ("image", "video", "audio"):
            assert m["cost_per_unit"] > 0


def test_platform_fee_math_direct_vs_aggregator() -> None:
    direct = get_model_by_id("gpt-4o")
    aggregator = get_model_by_id("openrouter/gpt-4o")
    assert direct is not None
    assert aggregator is not None

    bd_direct = calculate_cost_breakdown(direct, input_tokens=1_000_000, output_tokens=500_000)
    bd_agg = calculate_cost_breakdown(aggregator, input_tokens=1_000_000, output_tokens=500_000)

    assert bd_direct["base_usd"] == pytest.approx(7.5)
    assert bd_direct["platform_fee_usd"] == pytest.approx(0.0)
    assert bd_direct["total_usd"] == pytest.approx(7.5)

    # Aggregator base must equal direct base ($7.50) + 5.5% fee ($0.4125) = $7.9125
    assert bd_agg["base_usd"] == pytest.approx(7.5)
    assert bd_agg["platform_fee_usd"] == pytest.approx(7.5 * 0.055)
    assert bd_agg["total_usd"] == pytest.approx(7.9125)
    assert calculate_text_cost(aggregator, 1_000_000, 500_000) == pytest.approx(7.9125)


def test_cached_input_and_batch_discounts() -> None:
    opus = get_model_by_id("claude-opus-4.7")
    assert opus is not None

    # 200K uncached ($5/1M -> $1.00) + 800K cached ($0.50/1M -> $0.40) + 100K out ($25/1M -> $2.50) = $3.90
    bd = calculate_cost_breakdown(
        opus,
        input_tokens=200_000,
        cached_input_tokens=800_000,
        output_tokens=100_000,
        batch=True,
    )
    assert bd["raw_base_usd"] == pytest.approx(3.90)
    assert bd["batch_applied"] is True
    assert bd["batch_savings_usd"] == pytest.approx(1.95)
    assert bd["total_usd"] == pytest.approx(1.95)


def test_multimodal_and_gateway_calculations() -> None:
    veo = get_model_by_id("veo-3")
    whisper = get_model_by_id("whisper")
    portkey = get_model_by_id("portkey/gateway")
    martian = get_model_by_id("martian/router")

    assert calculate_image_cost(veo, 5) == pytest.approx(2.0)
    assert calculate_image_cost(whisper, 10.5) == pytest.approx(0.063)
    assert calculate_cost_breakdown(portkey, units=1)["total_usd"] == pytest.approx(499.0)
    assert calculate_cost_breakdown(martian)["is_custom_pricing"] is True


def test_aliases_and_fuzzy_suggestions() -> None:
    assert get_model_by_id("opus-4.7")["id"] == "claude-opus-4.7"
    assert get_model_by_id("r1")["id"] == "deepseek-r1"
    suggestions = suggest_similar_models("claude-sonnet")
    assert any("sonnet" in s for s in suggestions)


def test_recommender_excludes_legacy_and_gateways_by_default() -> None:
    recs = recommend_models("fast cheap coding", limit=5)
    assert len(recs) > 0
    for r in recs:
        assert "legacy" not in r.get("tags", [])
        assert r.get("type") != "gateway"

    gw_recs = recommend_models("enterprise gateway observability", limit=3)
    assert any(r.get("type") == "gateway" for r in gw_recs)


def test_monthly_budget_estimation() -> None:
    model = get_model_by_id("gemini-3.1-flash-lite")
    est = estimate_monthly_cost(model, requests_per_day=1000, avg_input_tokens=2000, avg_output_tokens=500, days=30)
    # Per req: (2000/1M)*0.25 + (500/1M)*1.5 = 0.0005 + 0.00075 = $0.00125
    assert est["per_request_usd"] == pytest.approx(0.00125)
    assert est["daily_usd"] == pytest.approx(1.25)
    assert est["period_total_usd"] == pytest.approx(37.5)


def test_currency_cache_creates_parent_directory(tmp_path: Path) -> None:
    import aicost.currency as currency_mod

    nested_dir = tmp_path / ".aicost_test"
    cache_file = nested_dir / "exchange_cache.json"
    with patch.object(currency_mod, "CACHE_DIR", nested_dir), patch.object(currency_mod, "CACHE_FILE", cache_file):
        currency_mod._save_cache({"USD": 1.0, "TRY": 40.0}, "2026-11-20")
        assert cache_file.exists()
        rate, curr = currency_mod.get_exchange_rate("try")
        assert curr == "TRY"
        assert rate == pytest.approx(40.0)


def test_cli_json_commands() -> None:
    res_ver = runner.invoke(app, ["--version"])
    assert res_ver.exit_code == 0
    assert __version__ in res_ver.stdout

    res_list = runner.invoke(app, ["list", "--provider", "Google", "--type", "image", "--json"])
    assert res_list.exit_code == 0
    parsed_list = json.loads(res_list.stdout)
    assert parsed_list["count"] >= 3

    res_calc = runner.invoke(app, ["calc", "openrouter/gpt-4o", "-i", "1000000", "-o", "500000", "--json"])
    assert res_calc.exit_code == 0
    parsed_calc = json.loads(res_calc.stdout)
    assert parsed_calc["total_cost"] == pytest.approx(7.9125)


def test_mcp_tools_and_resources() -> None:
    out_list, err_list = execute_mcp_tool("list_ai_models", {"provider": "DeepSeek", "include_legacy": False})
    assert not err_list
    assert "deepseek-v4-pro" in out_list
    assert "deepseek-v4.1-flash" in out_list

    out_calc, err_calc = execute_mcp_tool(
        "calculate_ai_cost",
        {"model_id": "openrouter/gpt-4o", "input_tokens": 1_000_000, "output_tokens": 500_000},
    )
    assert not err_calc
    assert json.loads(out_calc)["total_cost"] == pytest.approx(7.9125)

    out_cmp, err_cmp = execute_mcp_tool(
        "compare_ai_models",
        {"model_ids": ["gpt-6.2-astra", "claude-opus-5.5", "gemini-4-neon", "grok-4.7"]},
    )
    assert not err_cmp
    assert len(json.loads(out_cmp)["comparison"]) == 4

    mime, res_text = read_mcp_resource("aicost://pricing/metadata")
    assert mime == "application/json"
    assert json.loads(res_text)["model_count"] == len(get_pricing_data())
    assert get_all_data()["models"]


def test_frontier_2026_models_and_dynamic_openrouter_synthesis() -> None:
    astra = get_model_by_id("gpt-6.2-astra", allow_live=False)
    or_astra = get_model_by_id("openrouter/gpt-6.2-astra", allow_live=False)
    opus55 = get_model_by_id("claude-opus-5.5", allow_live=False)
    gemini4 = get_model_by_id("gemini-4-carbon", allow_live=False)
    grok47 = get_model_by_id("grok-4.7", allow_live=False)

    assert astra is not None and astra["cost_per_1m_input_tokens"] == pytest.approx(8.0)
    assert or_astra is not None and or_astra["platform_fee"] == pytest.approx(0.055)
    assert opus55 is not None and opus55["context_window"] == 1_000_000
    assert gemini4 is not None and gemini4["cost_per_1m_cached_input_tokens"] == pytest.approx(0.10)
    assert grok47 is not None and grok47["provider"] == "xAI"

    bd_direct = calculate_cost_breakdown(astra, input_tokens=1_000_000, output_tokens=0)
    bd_or = calculate_cost_breakdown(or_astra, input_tokens=1_000_000, output_tokens=0)
    assert bd_or["total_usd"] == pytest.approx(bd_direct["total_usd"] * 1.055)
