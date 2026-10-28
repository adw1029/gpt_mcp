"""
Lambda handler entrypoint — gr-gpt-customer (public borrower MCP).
Serves the static upload page at GET /upload, and delegates all
other requests to the MCP server.
"""
import os
import pathlib

from mcp_server.server import lambda_handler as _mcp_handler

_UPLOAD_HTML = (pathlib.Path(__file__).parent / "upload.html").read_text()


def lambda_handler(event, context):
    path = event.get("rawPath", "") or event.get("path", "")
    method = (event.get("requestContext", {}).get("http", {}).get("method", "GET")).upper()

    if path == "/upload" and method == "GET":
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "text/html; charset=utf-8"},
            "body": _UPLOAD_HTML,
        }

    return _mcp_handler(event, context)
