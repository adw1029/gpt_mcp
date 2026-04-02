"""
gr-gpt-customer MCP server entrypoint — public borrower-facing.
Tools are defined in src/mcp_server/tools/ — one file per tool.
Add a new tool by creating a new module and importing it in tools/__init__.py.
"""
import json
from mcp_server.registry import mcp
import mcp_server.tools  # noqa: F401 — registers all @mcp.tool() decorators

_CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
}


def lambda_handler(event, context):
    """AWS Lambda entrypoint."""
    method = event.get("requestContext", {}).get("http", {}).get("method", "").upper()

    if method == "OPTIONS":
        return {"statusCode": 200, "headers": _CORS_HEADERS, "body": ""}

    if not event.get("body"):
        return {
            "statusCode": 200,
            "headers": {**_CORS_HEADERS, "Content-Type": "application/json"},
            "body": json.dumps({"status": "ok", "service": "gr-borrower-mcp"}),
        }

    return mcp.handle_request(event, context)
