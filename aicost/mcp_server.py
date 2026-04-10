import mcp.server.stdio
from mcp.server import Server
from mcp.types import Tool, TextContent

from aicost.calculator import (
    get_pricing_data, 
    get_model_by_id, 
    calculate_text_cost, 
    calculate_image_cost,
    get_pricing_metadata
)
from aicost.currency import convert_cost, get_currency_date
from aicost.recommender import recommend_models

app = Server("aicost-mcp-server")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_ai_cost",
            description="Calculate the cost of an AI model usage based on tokens or units.",
            inputSchema={
                "type": "object",
                "properties": {
                    "model_id": {"type": "string", "description": "The ID of the model (e.g. 'gpt-4o', 'claude-3-5-sonnet')"},
                    "input_tokens": {"type": "integer", "description": "Number of input tokens (for text models)"},
                    "output_tokens": {"type": "integer", "description": "Number of output tokens (for text models)"},
                    "units": {"type": "integer", "description": "Number of units (for image models)"},
                    "currency": {"type": "string", "description": "Target currency code (e.g. 'USD', 'TRY')"}
                },
                "required": ["model_id"]
            }
        ),
        Tool(
            name="recommend_ai_model",
            description="Recommend AI models based on a task description. Use keywords like 'coding', 'cheap', 'fast', 'ocr', 'vision'.",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_description": {"type": "string", "description": "Description of the task to perform"},
                    "limit": {"type": "integer", "description": "Maximum number of models to recommend (default 3)"}
                },
                "required": ["task_description"]
            }
        ),
        Tool(
            name="compare_ai_models",
            description="Compare two AI models side-by-side to see which one is more cost-effective.",
            inputSchema={
                "type": "object",
                "properties": {
                    "model_id_1": {"type": "string", "description": "ID of the first model"},
                    "model_id_2": {"type": "string", "description": "ID of the second model"}
                },
                "required": ["model_id_1", "model_id_2"]
            }
        ),
        Tool(
            name="get_pricing_metadata",
            description="Get metadata about the current pricing database, such as the last update date.",
            inputSchema={"type": "object", "properties": {}}
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "get_ai_cost":
        model_id = arguments.get("model_id")
        input_tokens = arguments.get("input_tokens", 0)
        output_tokens = arguments.get("output_tokens", 0)
        units = arguments.get("units", 0)
        currency = arguments.get("currency", "USD")
        
        m = get_model_by_id(model_id)
        if not m:
            return [TextContent(type="text", text=f"Error: Model '{model_id}' not found.")]
            
        if m.get("type") == "text":
            usd_cost = calculate_text_cost(m, input_tokens, output_tokens)
        else:
            usd_cost = calculate_image_cost(m, units)
            
        final_cost = convert_cost(usd_cost, currency)
        
        return [TextContent(type="text", text=f"The cost for {model_id} is {final_cost:.4f} {currency.upper()}")]

    elif name == "recommend_ai_model":
        task = arguments.get("task_description")
        limit = arguments.get("limit", 3)
        
        models = recommend_models(task, limit=limit)
        
        if not models:
            return [TextContent(type="text", text="No suitable models found for this task.")]
            
        text_out = "Recommended models:\n"
        for i, m in enumerate(models):
            text_out += f"{i+1}. {m['id']} ({m['provider']}): {m['description']}\n"
            
        return [TextContent(type="text", text=text_out)]

    elif name == "compare_ai_models":
        m1 = get_model_by_id(arguments.get("model_id_1"))
        m2 = get_model_by_id(arguments.get("model_id_2"))
        
        if not m1 or not m2:
            return [TextContent(type="text", text="Error: One or both models not found.")]
            
        def fmt(m):
            return f"Provider: {m['provider']}, Input: ${m.get('cost_per_1m_input_tokens',0)}/1M, Output: ${m.get('cost_per_1m_output_tokens') or m.get('cost_per_unit',0)}"

        res = f"Comparison:\nModel 1 ({m1['id']}): {fmt(m1)}\nModel 2 ({m2['id']}): {fmt(m2)}"
        return [TextContent(type="text", text=res)]

    elif name == "get_pricing_metadata":
        meta = get_pricing_metadata()
        cur_date = get_currency_date()
        res = f"Data Updated: {meta.get('last_updated', 'Unknown')}\nCurrency Matched: {cur_date}"
        return [TextContent(type="text", text=res)]
        
    raise ValueError(f"Tool {name} is not supported")

def start_server():
    import asyncio
    
    async def run():
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            import sys
            # Write to stderr to avoid corrupting MCP stdio JSON-RPC
            sys.stderr.write("Starting AI-Cost-CLI MCP Server...\n")
            await app.run(read_stream, write_stream, app.create_initialization_options())
            
    asyncio.run(run())
