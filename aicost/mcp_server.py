from __future__ import annotations

import warnings
warnings.filterwarnings("ignore", message=".*urllib3 v2 only supports OpenSSL 1.1.1+.*")

import json
import sys
from typing import Any

from aicost import __version__
from aicost.calculator import (
    calculate_cost_breakdown,
    estimate_monthly_cost,
    fetch_live_catalog,
    fetch_remote_pricing,
    filter_models,
    format_unit_label,
    get_all_data,
    get_effective_rates,
    get_model_by_id,
    get_pricing_metadata,
    suggest_similar_models,
)
from aicost.currency import get_currency_date, get_exchange_rate, refresh_rates
from aicost.recommender import recommend_models

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "list_ai_models",
        "description": (
            "List AI models and their effective pricing across text, image, video, audio, and gateway providers. "
            "Supports filtering by provider, type, capability tag, and currency conversion."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "provider": {
                    "type": "string",
                    "description": "Filter by provider name (e.g., 'OpenAI', 'Anthropic', 'Google', 'DeepSeek', 'OpenRouter')",
                },
                "model_type": {
                    "type": "string",
                    "enum": ["text", "image", "video", "audio", "gateway"],
                    "description": "Filter by modality/model type",
                },
                "tag": {
                    "type": "string",
                    "description": "Filter by capability tag (e.g., 'coding', 'cheap', 'fast', 'agentic', 'vision', 'reasoning')",
                },
                "include_legacy": {
                    "type": "boolean",
                    "description": "Include older/superseded models tagged as legacy (default: false)",
                },
                "include_live": {
                    "type": "boolean",
                    "description": "Include 400+ live models from OpenRouter catalog in addition to curated models (default: false)",
                },
                "currency": {
                    "type": "string",
                    "description": "Target currency code (e.g., 'USD', 'TRY', 'EUR', 'GBP'). Defaults to 'USD'.",
                },
            },
        },
    },
    {
        "name": "calculate_ai_cost",
        "description": (
            "Calculate the exact cost of an AI API call with full base cost, prompt-caching, batch discount, "
            "and aggregator platform fee breakdown. Supports 60+ curated models and 400+ live OpenRouter models."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "model_id": {
                    "type": "string",
                    "description": "Model ID or alias (e.g., 'gpt-6.2-astra', 'claude-opus-5.5', 'gemini-4-carbon', 'grok-4.7', 'deepseek-v4.1-flash', 'veo-3.1')",
                },
                "input_tokens": {"type": "integer", "description": "Uncached input tokens (for text models)"},
                "cached_input_tokens": {"type": "integer", "description": "Cached input tokens billed at cache-read rate"},
                "output_tokens": {"type": "integer", "description": "Output completion tokens (for text models)"},
                "units": {
                    "type": "number",
                    "description": "Number of units for non-text models (images, seconds, minutes, songs, clips, 1M chars, or months)",
                },
                "batch": {"type": "boolean", "description": "Apply Batch API discount if supported (default: false)"},
                "currency": {"type": "string", "description": "Target currency code (default: 'USD')"},
            },
            "required": ["model_id"],
        },
    },
    {
        "name": "get_ai_cost",
        "description": "Alias for calculate_ai_cost: calculate the cost of an AI model usage based on tokens or units.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "model_id": {"type": "string", "description": "Model ID (e.g., 'claude-opus-4.7', 'gpt-5.5', 'deepseek-r1')"},
                "input_tokens": {"type": "integer", "description": "Number of input tokens (for text models)"},
                "cached_input_tokens": {"type": "integer", "description": "Number of cached input tokens"},
                "output_tokens": {"type": "integer", "description": "Number of output tokens (for text models)"},
                "units": {"type": "number", "description": "Number of units (for image/video/audio models)"},
                "batch": {"type": "boolean", "description": "Apply Batch API discount if supported"},
                "currency": {"type": "string", "description": "Target currency code (e.g., 'USD', 'TRY')"},
            },
            "required": ["model_id"],
        },
    },
    {
        "name": "compare_ai_models",
        "description": "Compare two or more AI models side-by-side on pricing, platform fees, context window, and workload cost.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "model_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of two or more model IDs to compare (e.g., ['claude-opus-4.7', 'gpt-5.5', 'gemini-3.1-pro'])",
                },
                "model_id_1": {"type": "string", "description": "First model ID (legacy 2-model parameter)"},
                "model_id_2": {"type": "string", "description": "Second model ID (legacy 2-model parameter)"},
                "input_tokens": {"type": "integer", "description": "Optional sample input tokens to compare actual call cost"},
                "output_tokens": {"type": "integer", "description": "Optional sample output tokens to compare actual call cost"},
                "units": {"type": "number", "description": "Optional sample units to compare non-text call cost"},
                "currency": {"type": "string", "description": "Target currency code (default: 'USD')"},
            },
        },
    },
    {
        "name": "recommend_ai_model",
        "description": (
            "Recommend the best cost-effective AI models for a task description. "
            "Supports keywords like 'coding', 'cheap', 'fast', 'agentic', 'vision', 'reasoning', 'video', 'image', 'music'."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_description": {"type": "string", "description": "Description of the workload or task"},
                "limit": {"type": "integer", "description": "Maximum number of recommendations (default: 3)"},
                "model_type": {
                    "type": "string",
                    "enum": ["text", "image", "video", "audio", "gateway"],
                    "description": "Optional modality filter",
                },
                "max_input_cost": {
                    "type": "number",
                    "description": "Optional maximum USD cost per 1M input tokens (or per unit)",
                },
                "include_legacy": {"type": "boolean", "description": "Include legacy models (default: false)"},
                "currency": {"type": "string", "description": "Target currency code (default: 'USD')"},
            },
            "required": ["task_description"],
        },
    },
    {
        "name": "estimate_monthly_cost",
        "description": "Estimate daily, monthly, and annual AI API costs for a recurring production workload.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "model_id": {"type": "string", "description": "Model ID or alias"},
                "requests_per_day": {"type": "number", "description": "Average requests per day"},
                "avg_input_tokens": {"type": "integer", "description": "Average uncached input tokens per request"},
                "avg_cached_input_tokens": {"type": "integer", "description": "Average cached input tokens per request"},
                "avg_output_tokens": {"type": "integer", "description": "Average output tokens per request"},
                "avg_units": {"type": "number", "description": "Average units per request (for non-text models)"},
                "days": {"type": "integer", "description": "Days in billing cycle (default: 30)"},
                "batch": {"type": "boolean", "description": "Whether requests use Batch API (default: false)"},
                "currency": {"type": "string", "description": "Target currency code (default: 'USD')"},
            },
            "required": ["model_id", "requests_per_day"],
        },
    },
    {
        "name": "get_pricing_metadata",
        "description": "Get metadata about the current pricing database (schema version, model count, last update date, currency cache timestamp).",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "sync_pricing_data",
        "description": "Fetch the latest pricing database from GitHub and refresh live currency exchange rates.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]

RESOURCE_DEFINITIONS: list[dict[str, str]] = [
    {
        "uri": "aicost://pricing/models",
        "name": "AI Models Pricing Catalog",
        "description": "Complete JSON catalog of AI model prices, context windows, billing units, and platform fees.",
        "mimeType": "application/json",
    },
    {
        "uri": "aicost://pricing/metadata",
        "name": "Pricing & Currency Metadata",
        "description": "Current pricing database version, last update date, and currency rate cache timestamp.",
        "mimeType": "application/json",
    },
]


def read_mcp_resource(uri: str) -> tuple[str, str]:
    """Returns (mime_type, json_text) for a supported MCP resource URI."""
    if uri == "aicost://pricing/models":
        return "application/json", json.dumps(get_all_data(), indent=2)
    if uri == "aicost://pricing/metadata":
        meta = get_pricing_metadata()
        meta["currency_cached_at"] = get_currency_date()
        meta["server_version"] = __version__
        return "application/json", json.dumps(meta, indent=2)
    raise ValueError(f"Unknown resource URI: {uri}")


def execute_mcp_tool(name: str, arguments: dict[str, Any] | None) -> tuple[str, bool]:
    """Executes a tool by name and returns (formatted_text, is_error)."""
    args = arguments or {}

    if name == "list_ai_models":
        models = filter_models(
            provider=args.get("provider"),
            model_type=args.get("model_type"),
            tag=args.get("tag"),
            include_legacy=bool(args.get("include_legacy", False)),
            include_live=bool(args.get("include_live", False)),
            sort_by="input",
        )
        rate, curr = get_exchange_rate(args.get("currency", "USD"))
        meta = get_pricing_metadata()
        payload = {
            "currency": curr,
            "last_updated": meta.get("last_updated"),
            "count": len(models),
            "models": [
                {
                    "id": m["id"],
                    "provider": m.get("provider"),
                    "type": m.get("type", "text"),
                    "source_type": m.get("source_type", "direct"),
                    "billing_unit": m.get("billing_unit"),
                    "context_window": m.get("context_window"),
                    "platform_fee": m.get("platform_fee", 0.0),
                    "effective_input_per_1m": (
                        round(get_effective_rates(m)["input_per_1m"] * rate, 6)
                        if get_effective_rates(m)["input_per_1m"] is not None
                        else None
                    ),
                    "effective_cached_input_per_1m": (
                        round(get_effective_rates(m)["cached_input_per_1m"] * rate, 6)
                        if get_effective_rates(m)["cached_input_per_1m"] is not None
                        else None
                    ),
                    "effective_output_per_1m": (
                        round(get_effective_rates(m)["output_per_1m"] * rate, 6)
                        if get_effective_rates(m)["output_per_1m"] is not None
                        else None
                    ),
                    "effective_unit_cost": (
                        round(get_effective_rates(m)["per_unit"] * rate, 6)
                        if get_effective_rates(m)["per_unit"] is not None
                        else None
                    ),
                    "fixed_monthly_cost": (
                        round(get_effective_rates(m)["monthly"] * rate, 2)
                        if get_effective_rates(m)["monthly"] is not None
                        else None
                    ),
                    "tags": m.get("tags", []),
                }
                for m in models
            ],
        }
        return json.dumps(payload, indent=2), False

    if name in ("calculate_ai_cost", "get_ai_cost"):
        model_id = str(args.get("model_id", "")).strip()
        m = get_model_by_id(model_id)
        if not m:
            suggestions = suggest_similar_models(model_id)
            hint = f" Did you mean: {', '.join(suggestions)}?" if suggestions else ""
            return f"Error: Model '{model_id}' not found.{hint}", True

        bd = calculate_cost_breakdown(
            model=m,
            input_tokens=int(args.get("input_tokens", 0) or 0),
            output_tokens=int(args.get("output_tokens", 0) or 0),
            cached_input_tokens=int(args.get("cached_input_tokens", 0) or 0),
            units=float(args.get("units", 0) or 0.0),
            batch=bool(args.get("batch", False)),
        )
        rate, curr = get_exchange_rate(args.get("currency", "USD"))
        result = {
            "model_id": bd["model_id"],
            "provider": bd["provider"],
            "source_type": bd["source_type"],
            "usage_summary": bd["usage_summary"],
            "currency": curr,
            "is_custom_pricing": bd["is_custom_pricing"],
            "base_cost": round(bd["base_usd"] * rate, 6),
            "batch_applied": bd["batch_applied"],
            "batch_savings": round(bd["batch_savings_usd"] * rate, 6),
            "platform_fee_rate": bd["platform_fee_rate"],
            "platform_fee_cost": round(bd["platform_fee_usd"] * rate, 6),
            "total_cost": round(bd["total_usd"] * rate, 6),
        }
        return json.dumps(result, indent=2), False

    if name == "compare_ai_models":
        raw_ids: list[str] = list(args.get("model_ids") or [])
        if not raw_ids:
            if args.get("model_id_1"):
                raw_ids.append(str(args["model_id_1"]))
            if args.get("model_id_2"):
                raw_ids.append(str(args["model_id_2"]))

        if len(raw_ids) < 2:
            return "Error: Provide at least two models via 'model_ids' (or 'model_id_1' and 'model_id_2').", True

        resolved = []
        for mid in raw_ids:
            m = get_model_by_id(mid)
            if not m:
                suggestions = suggest_similar_models(mid)
                hint = f" Did you mean: {', '.join(suggestions)}?" if suggestions else ""
                return f"Error: Model '{mid}' not found.{hint}", True
            resolved.append(m)

        rate, curr = get_exchange_rate(args.get("currency", "USD"))
        sample_in = int(args.get("input_tokens", 0) or 0)
        sample_out = int(args.get("output_tokens", 0) or 0)
        sample_units = float(args.get("units", 0) or 0.0)
        has_workload = sample_in > 0 or sample_out > 0 or sample_units > 0

        entries = []
        for m in resolved:
            eff = get_effective_rates(m)
            unit_lbl = format_unit_label(m.get("billing_unit"), m.get("type", "text"))
            entry: dict[str, Any] = {
                "id": m["id"],
                "provider": m.get("provider"),
                "source_type": m.get("source_type", "direct"),
                "platform_fee": eff["platform_fee"],
                "type": m.get("type", "text"),
                "billing_unit": unit_lbl,
                "context_window": m.get("context_window"),
                "effective_input_per_1m": round(eff["input_per_1m"] * rate, 6) if eff["input_per_1m"] is not None else None,
                "effective_cached_input_per_1m": (
                    round(eff["cached_input_per_1m"] * rate, 6) if eff["cached_input_per_1m"] is not None else None
                ),
                "effective_output_per_1m": round(eff["output_per_1m"] * rate, 6) if eff["output_per_1m"] is not None else None,
                "effective_unit_cost": round(eff["per_unit"] * rate, 6) if eff["per_unit"] is not None else None,
                "fixed_monthly_cost": round(eff["monthly"] * rate, 2) if eff["monthly"] is not None else None,
                "tags": m.get("tags", []),
            }
            if has_workload:
                bd = calculate_cost_breakdown(m, input_tokens=sample_in, output_tokens=sample_out, units=sample_units)
                entry["sample_workload_cost"] = round(bd["total_usd"] * rate, 6)
            entries.append(entry)

        return json.dumps({"currency": curr, "comparison": entries}, indent=2), False

    if name == "recommend_ai_model":
        task = str(args.get("task_description", "")).strip()
        limit = int(args.get("limit", 3) or 3)
        models = recommend_models(
            task_description=task,
            limit=limit,
            model_type=args.get("model_type"),
            max_input_cost=float(args["max_input_cost"]) if args.get("max_input_cost") is not None else None,
            include_legacy=bool(args.get("include_legacy", False)),
        )
        if not models:
            return "No suitable models matched the given task and constraints.", False

        rate, curr = get_exchange_rate(args.get("currency", "USD"))
        recs = []
        for idx, m in enumerate(models, 1):
            eff = get_effective_rates(m)
            recs.append({
                "rank": idx,
                "id": m["id"],
                "provider": m.get("provider"),
                "type": m.get("type", "text"),
                "description": m.get("description", ""),
                "tags": m.get("tags", []),
                "effective_input_per_1m": round(eff["input_per_1m"] * rate, 6) if eff["input_per_1m"] is not None else None,
                "effective_output_per_1m": round(eff["output_per_1m"] * rate, 6) if eff["output_per_1m"] is not None else None,
                "effective_unit_cost": round(eff["per_unit"] * rate, 6) if eff["per_unit"] is not None else None,
            })
        return json.dumps({"task": task, "currency": curr, "recommendations": recs}, indent=2), False

    if name == "estimate_monthly_cost":
        model_id = str(args.get("model_id", "")).strip()
        m = get_model_by_id(model_id)
        if not m:
            suggestions = suggest_similar_models(model_id)
            hint = f" Did you mean: {', '.join(suggestions)}?" if suggestions else ""
            return f"Error: Model '{model_id}' not found.{hint}", True

        est = estimate_monthly_cost(
            model=m,
            requests_per_day=float(args.get("requests_per_day", 0) or 0),
            avg_input_tokens=int(args.get("avg_input_tokens", 0) or 0),
            avg_output_tokens=int(args.get("avg_output_tokens", 0) or 0),
            avg_cached_input_tokens=int(args.get("avg_cached_input_tokens", 0) or 0),
            avg_units=float(args.get("avg_units", 0) or 0.0),
            days=int(args.get("days", 30) or 30),
            batch=bool(args.get("batch", False)),
        )
        rate, curr = get_exchange_rate(args.get("currency", "USD"))
        return json.dumps({
            "model_id": est["model_id"],
            "provider": est["provider"],
            "currency": curr,
            "requests_per_day": est["requests_per_day"],
            "days": est["days"],
            "per_request_cost": round(est["per_request_usd"] * rate, 6),
            "daily_cost": round(est["daily_usd"] * rate, 4),
            "period_base_cost": round(est["period_base_usd"] * rate, 4),
            "period_fee_cost": round(est["period_fee_usd"] * rate, 4),
            "period_total_cost": round(est["period_total_usd"] * rate, 4),
            "annual_total_cost": round(est["annual_total_usd"] * rate, 2),
            "period_requests": est["period_requests"],
            "period_input_tokens": est["period_input_tokens"],
            "period_output_tokens": est["period_output_tokens"],
        }, indent=2), False

    if name == "get_pricing_metadata":
        meta = get_pricing_metadata()
        meta["currency_cached_at"] = get_currency_date()
        meta["server_version"] = __version__
        return json.dumps(meta, indent=2), False

    if name == "sync_pricing_data":
        data = fetch_remote_pricing()
        live_models = fetch_live_catalog()
        rates = refresh_rates()
        return json.dumps({
            "pricing_synced": bool(data),
            "last_updated": data.get("last_updated") if data else get_pricing_metadata().get("last_updated"),
            "live_catalog_synced": len(live_models) > 0,
            "live_catalog_count": len(live_models),
            "currencies_synced": len(rates) > 1,
            "currency_count": len(rates),
        }, indent=2), not bool(data or live_models)

    return f"Unsupported tool: {name}", True


def _run_minimal_stdio_jsonrpc() -> None:
    """
    Lightweight MCP JSON-RPC 2.0 stdio fallback for Python 3.9 environments where
    the external 'mcp' package (Python >= 3.10) is unavailable.
    """
    sys.stderr.write(f"Starting AI-Cost-CLI MCP Server v{__version__} (stdio fallback)...\n")
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except Exception:
            continue

        req_id = msg.get("id")
        method = msg.get("method", "")
        params = msg.get("params") or {}

        # Notifications do not carry an id and require no response
        if req_id is None:
            continue

        result: Any = None
        error_obj: dict[str, Any] | None = None

        try:
            if method == "initialize":
                result = {
                    "protocolVersion": params.get("protocolVersion", "2024-11-05"),
                    "capabilities": {"tools": {}, "resources": {}},
                    "serverInfo": {"name": "aicost-mcp-server", "version": __version__},
                }
            elif method == "ping":
                result = {}
            elif method == "tools/list":
                result = {"tools": TOOL_DEFINITIONS}
            elif method == "tools/call":
                text, is_error = execute_mcp_tool(params.get("name", ""), params.get("arguments"))
                result = {"content": [{"type": "text", "text": text}], "isError": is_error}
            elif method == "resources/list":
                result = {"resources": RESOURCE_DEFINITIONS}
            elif method == "resources/read":
                uri = str(params.get("uri", ""))
                mime_type, text = read_mcp_resource(uri)
                result = {"contents": [{"uri": uri, "mimeType": mime_type, "text": text}]}
            else:
                error_obj = {"code": -32601, "message": f"Method not found: {method}"}
        except Exception as exc:
            error_obj = {"code": -32603, "message": str(exc)}

        resp: dict[str, Any] = {"jsonrpc": "2.0", "id": req_id}
        if error_obj is not None:
            resp["error"] = error_obj
        else:
            resp["result"] = result

        sys.stdout.write(json.dumps(resp) + "\n")
        sys.stdout.flush()


def start_server() -> None:
    """Starts the MCP stdio server using the official MCP SDK when available, or stdio fallback."""
    try:
        import asyncio
        import mcp.server.stdio
        from mcp.server import Server
        from mcp.types import CallToolResult, Resource, TextContent, Tool
    except ImportError:
        _run_minimal_stdio_jsonrpc()
        return

    server = Server("aicost-mcp-server")

    @server.list_tools()
    async def handle_list_tools() -> list[Tool]:
        return [
            Tool(
                name=t["name"],
                description=t["description"],
                inputSchema=t["inputSchema"],
            )
            for t in TOOL_DEFINITIONS
        ]

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict[str, Any] | None) -> Any:
        text, is_error = execute_mcp_tool(name, arguments)
        if is_error:
            return CallToolResult(
                content=[TextContent(type="text", text=text)],
                isError=True,
            )
        return [TextContent(type="text", text=text)]

    @server.list_resources()
    async def handle_list_resources() -> list[Resource]:
        return [
            Resource(
                uri=r["uri"],
                name=r["name"],
                description=r["description"],
                mimeType=r["mimeType"],
            )
            for r in RESOURCE_DEFINITIONS
        ]

    @server.read_resource()
    async def handle_read_resource(uri: Any) -> str:
        _, text = read_mcp_resource(str(uri))
        return text

    async def run() -> None:
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            sys.stderr.write(f"Starting AI-Cost-CLI MCP Server v{__version__}...\n")
            await server.run(read_stream, write_stream, server.create_initialization_options())

    asyncio.run(run())


if __name__ == "__main__":
    start_server()
