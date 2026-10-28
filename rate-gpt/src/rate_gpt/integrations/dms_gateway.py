"""Client for the digital-mortgage-systems tools on Rate's partner gateway.

Every tool is `POST {base}/{tool}` with a JSON body. Responses wrap the real
payload as a JSON *string* in `result`:

    {"tool": "create_loan", "success": true, "request_id": "...",
     "result": "{\"success\": true, \"data\": {\"loanId\": \"...\"}}"}
"""
import json
import logging
from collections.abc import Callable
from typing import Any

import httpx

from rate_gpt.errors import IntegrationError

log = logging.getLogger(__name__)


class DmsGatewayClient:
    def __init__(
        self,
        base_url: str,
        token: Callable[[], str],
        http: httpx.Client,
        on_unauthorized: Callable[[], None] | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._http = http
        self._on_unauthorized = on_unauthorized

    def call(self, tool: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Call a gateway tool and return the parsed inner result."""
        resp = self._post(tool, payload)
        if resp.status_code == 401 and self._on_unauthorized:
            # Token was revoked or expired early: refresh once and retry.
            self._on_unauthorized()
            resp = self._post(tool, payload)

        # Log status and request ID only. Payloads and bodies carry borrower NPI.
        request_id = _safe_json(resp).get("request_id")
        if resp.status_code != 200:
            log.error("Gateway %s returned HTTP %s (request_id=%s)", tool, resp.status_code, request_id)
            raise IntegrationError("The loan system returned an error. Please try again.")

        outer = resp.json()
        inner = outer.get("result")
        if isinstance(inner, str):
            try:
                inner = json.loads(inner)
            except json.JSONDecodeError:
                inner = {}
        inner = inner or {}
        if not outer.get("success") or not inner.get("success", False):
            log.error("Gateway %s reported failure (request_id=%s)", tool, request_id)
            raise IntegrationError("The loan system couldn't process that request. Please try again.")
        log.info("Gateway %s ok (request_id=%s)", tool, request_id)
        return inner

    def _post(self, tool: str, payload: dict[str, Any]) -> httpx.Response:
        try:
            return self._http.post(
                f"{self._base_url}/{tool}",
                json=payload,
                headers={"Authorization": f"Bearer {self._token()}", "Accept": "application/json"},
            )
        except httpx.HTTPError as exc:
            log.error("Gateway %s request failed: %s", tool, type(exc).__name__)
            raise IntegrationError("We couldn't reach the loan system. Please try again.") from exc


def _safe_json(resp: httpx.Response) -> dict[str, Any]:
    try:
        body = resp.json()
        return body if isinstance(body, dict) else {}
    except ValueError:
        return {}
