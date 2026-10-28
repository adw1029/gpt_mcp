"""Okta client-credentials tokens for calling Rate's partner gateway.

Credentials come from SSM. Tokens are cached in memory and, when a table is
configured, in DynamoDB so warm and cold Lambda instances share one token.
"""
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from rate_gpt.errors import IntegrationError

log = logging.getLogger(__name__)

PLACEHOLDER = "REPLACE_ME"
# Refresh this many seconds before the token actually expires.
_EXPIRY_MARGIN = 60


@dataclass(frozen=True)
class CachedToken:
    access_token: str
    expires_at: int  # epoch seconds

    def is_fresh(self, now: float) -> bool:
        return now < self.expires_at - _EXPIRY_MARGIN


class TokenCache(Protocol):
    def get(self) -> CachedToken | None: ...

    def put(self, token: CachedToken) -> None: ...


class DynamoTokenCache:
    """One item per token in a table keyed by `name`, expiring via TTL on `expiresAt`."""

    def __init__(self, table: Any, key: str) -> None:
        self._table = table
        self._key = key

    @classmethod
    def create(cls, table_name: str, key: str) -> "DynamoTokenCache":
        import boto3

        return cls(boto3.resource("dynamodb").Table(table_name), key)

    def get(self) -> CachedToken | None:
        item = self._table.get_item(Key={"name": self._key}).get("Item")
        if not item:
            return None
        return CachedToken(access_token=item["accessToken"], expires_at=int(item["expiresAt"]))

    def put(self, token: CachedToken) -> None:
        self._table.put_item(
            Item={"name": self._key, "accessToken": token.access_token, "expiresAt": token.expires_at}
        )


def ssm_credentials(client_id_param: str, client_secret_param: str) -> Callable[[], tuple[str, str]]:
    """Read the client ID and secret from SSM (String or SecureString)."""

    def load() -> tuple[str, str]:
        import boto3

        ssm = boto3.client("ssm")
        params = ssm.get_parameters(Names=[client_id_param, client_secret_param], WithDecryption=True)
        values = {p["Name"]: p["Value"] for p in params["Parameters"]}
        client_id, secret = values.get(client_id_param), values.get(client_secret_param)
        if not client_id or not secret or PLACEHOLDER in (client_id, secret):
            log.error("Okta credentials missing or still placeholders in SSM")
            raise IntegrationError("The loan system isn't configured yet. Please try again later.")
        return client_id, secret

    return load


class ClientCredentialsTokenProvider:
    def __init__(
        self,
        token_url: str,
        scope: str,
        credentials: Callable[[], tuple[str, str]],
        http: httpx.Client,
        cache: TokenCache | None = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._token_url = token_url
        self._scope = scope
        self._credentials = credentials
        self._http = http
        self._cache = cache
        self._clock = clock
        self._memory: CachedToken | None = None

    def token(self) -> str:
        now = self._clock()
        if self._memory and self._memory.is_fresh(now):
            return self._memory.access_token
        if self._cache and (shared := self._safe_cache_get()) and shared.is_fresh(now):
            self._memory = shared
            return shared.access_token

        self._memory = self._fetch(now)
        if self._cache:
            self._safe_cache_put(self._memory)
        return self._memory.access_token

    def invalidate(self) -> None:
        self._memory = None

    def _fetch(self, now: float) -> CachedToken:
        client_id, secret = self._credentials()
        try:
            resp = self._http.post(
                self._token_url,
                data={"grant_type": "client_credentials", "scope": self._scope},
                auth=(client_id, secret),
                headers={"Accept": "application/json"},
            )
        except httpx.HTTPError as exc:
            log.error("Okta token request failed: %s", type(exc).__name__)
            raise IntegrationError("We couldn't reach the loan system. Please try again.") from exc
        if resp.status_code != 200:
            # Okta error bodies hold an error code, never the secret.
            log.error("Okta token request returned %s: %s", resp.status_code, resp.text[:300])
            raise IntegrationError("We couldn't reach the loan system. Please try again.")
        body = resp.json()
        return CachedToken(access_token=body["access_token"], expires_at=int(now + body.get("expires_in", 3600)))

    # The cache is an optimization: if DynamoDB is unavailable, fetch a fresh token instead of failing.
    def _safe_cache_get(self) -> CachedToken | None:
        try:
            return self._cache.get()
        except Exception:
            log.warning("Token cache read failed", exc_info=True)
            return None

    def _safe_cache_put(self, token: CachedToken) -> None:
        try:
            self._cache.put(token)
        except Exception:
            log.warning("Token cache write failed", exc_info=True)
