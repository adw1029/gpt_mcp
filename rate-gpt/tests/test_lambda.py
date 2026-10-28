"""The Lambda handler, driven with API Gateway HTTP API (payload v2) events."""
import base64
import importlib
import json

import pytest

INIT = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "test", "version": "0"},
    },
}


def http_api_event(body: dict) -> dict:
    return {
        "version": "2.0",
        "routeKey": "ANY /mcp",
        "rawPath": "/mcp",
        "rawQueryString": "",
        "headers": {
            "host": "abc123.execute-api.us-east-1.amazonaws.com",
            "content-type": "application/json",
            "accept": "application/json, text/event-stream",
            "mcp-protocol-version": "2025-06-18",
        },
        "requestContext": {
            "http": {"method": "POST", "path": "/mcp", "protocol": "HTTP/1.1", "sourceIp": "1.2.3.4", "userAgent": "t"},
            "stage": "$default",
            "domainName": "abc123.execute-api.us-east-1.amazonaws.com",
            "requestId": "r",
            "routeKey": "ANY /mcp",
        },
        "body": json.dumps(body),
        "isBase64Encoded": False,
    }


def body_of(response: dict) -> dict:
    raw = response["body"]
    if response.get("isBase64Encoded"):
        raw = base64.b64decode(raw).decode()
    return json.loads(raw)


@pytest.fixture
def lambda_module(monkeypatch):
    # Memory + demo backends: exercises the HTTP path without AWS or the gateway.
    monkeypatch.setenv("RATE_GPT_DATA_BACKEND", "memory")
    monkeypatch.setenv("RATE_GPT_LOS_BACKEND", "demo")
    import rate_gpt.lambda_handler as module

    return importlib.reload(module)


def test_initialize_and_list_tools_across_warm_invocations(lambda_module):
    init = lambda_module.handler(http_api_event(INIT), None)
    assert init["statusCode"] == 200
    assert body_of(init)["result"]["serverInfo"]["name"] == "rate-gpt"

    # A second invocation on the same warm instance must work too (fresh session manager).
    listed = lambda_module.handler(http_api_event({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}), None)
    assert listed["statusCode"] == 200
    names = {t["name"] for t in body_of(listed)["result"]["tools"]}
    assert names == {
        "save_loan_application",
        "submit_loan_application",
        "get_application_status",
        "create_portal_account",
    }


def test_tool_call_over_lambda(lambda_module):
    call = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {"name": "get_application_status", "arguments": {"application_id": "RG-100001"}},
    }
    response = lambda_module.handler(http_api_event(call), None)
    result = body_of(response)["result"]
    assert not result.get("isError")
    assert result["structuredContent"]["stage"] == "conditionally_approved"
    assert result["structuredContent"]["upload_documents_url"] == "https://my.owning.com/login"


@pytest.mark.parametrize("method", ["GET", "DELETE"])
def test_non_post_is_refused_immediately(lambda_module, method):
    # ChatGPT opens GET /mcp for server events; a stateless server must refuse
    # it fast instead of holding it open until the Lambda timeout.
    event = http_api_event({})
    event["requestContext"]["http"]["method"] = method
    event["headers"]["accept"] = "text/event-stream"
    event["body"] = ""
    response = lambda_module.handler(event, None)
    assert response["statusCode"] == 405
    assert response["headers"]["allow"] == "POST"
