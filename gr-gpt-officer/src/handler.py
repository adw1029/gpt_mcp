"""
Lambda handler entrypoint — gr-gpt-officer (internal LO MCP).
API Gateway invokes this; the handler delegates to the MCP server.
"""
from mcp_server.server import lambda_handler

__all__ = ["lambda_handler"]
