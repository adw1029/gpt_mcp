"""External systems. Services depend on the protocols here, never on a concrete client."""
from typing import NamedTuple

import httpx

from rate_gpt.config import Settings
from rate_gpt.integrations.accounts import BorrowerAccounts
from rate_gpt.integrations.los import LoanOriginationSystem


class Integrations(NamedTuple):
    los: LoanOriginationSystem
    accounts: BorrowerAccounts


def build_integrations(settings: Settings) -> Integrations:
    match settings.los_backend:
        case "demo":
            from rate_gpt.integrations.accounts import DemoBorrowerAccounts
            from rate_gpt.integrations.los import DemoLoanOriginationSystem

            return Integrations(DemoLoanOriginationSystem(), DemoBorrowerAccounts())
        case "gateway":
            from rate_gpt.integrations.accounts import GatewayBorrowerAccounts
            from rate_gpt.integrations.dms_gateway import DmsGatewayClient
            from rate_gpt.integrations.los import GatewayLoanOriginationSystem
            from rate_gpt.integrations.okta import (
                ClientCredentialsTokenProvider,
                DynamoTokenCache,
                ssm_credentials,
            )

            http = httpx.Client(timeout=httpx.Timeout(20.0, connect=5.0))
            cache = (
                DynamoTokenCache.create(settings.token_table, settings.token_cache_key)
                if settings.token_table
                else None
            )
            tokens = ClientCredentialsTokenProvider(
                token_url=settings.okta_token_url,
                scope=settings.okta_scope,
                credentials=ssm_credentials(settings.okta_client_id_param, settings.okta_client_secret_param),
                http=http,
                cache=cache,
            )
            # One gateway client (and one token) shared by every integration.
            gateway = DmsGatewayClient(settings.gateway_url, tokens.token, http, on_unauthorized=tokens.invalidate)
            return Integrations(
                GatewayLoanOriginationSystem(gateway, settings.gateway_company, settings.gateway_company_eid),
                GatewayBorrowerAccounts(gateway, settings.gateway_company),
            )
        case other:
            raise ValueError(f"Unknown LOS backend: {other!r}")
