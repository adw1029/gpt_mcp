"""AWS Lambda entrypoint: API Gateway (HTTP API) -> MCP Streamable HTTP.

Runs stateless with plain JSON responses, so every request is self-contained
and any Lambda instance can serve it. The server (and its clients and caches)
is built once per cold start. The HTTP app is rebuilt per invocation because
the SDK's session manager can only be started once, and Mangum runs the ASGI
lifespan on every invocation.
"""
import logging

from mangum import Mangum

from rate_gpt.server import build_server

logging.getLogger().setLevel(logging.INFO)

_server = build_server()


def handler(event, context):
    # Stateless servers have no server-to-client stream to offer. Without this,
    # the SDK holds a GET (SSE) open until Lambda times out; the spec allows 405.
    if event.get("requestContext", {}).get("http", {}).get("method") != "POST":
        return {"statusCode": 405, "headers": {"allow": "POST"}, "body": ""}
    # host="0.0.0.0" turns off the SDK's localhost-only Host check; API Gateway
    # is the front door here, and it sends its own execute-api Host header.
    app = _server.streamable_http_app(stateless_http=True, json_response=True, host="0.0.0.0")
    return Mangum(app, lifespan="on", api_gateway_base_path="/")(event, context)
