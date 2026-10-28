"""Runtime settings, read from environment variables (see .env.example)."""
import os
from dataclasses import dataclass, field


def _csv(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


@dataclass(frozen=True)
class Settings:
    # Feature modules to load, in order. Each name is a package under rate_gpt.modules.
    modules: list[str] = field(default_factory=lambda: ["applications", "status", "accounts"])
    # Storage backend for repositories: "memory" (local) or "dynamodb" (deployed).
    data_backend: str = "memory"
    # Load demo records from data/seed/ at startup (memory backend only).
    seed_demo_data: bool = True
    applications_table: str = ""
    host: str = "127.0.0.1"
    port: int = 8000
    # Extra Host headers to accept, e.g. an ngrok domain when testing from ChatGPT.
    public_hosts: list[str] = field(default_factory=list)

    # Where submitted applications go: "demo" (fake loan IDs) or "gateway" (DMS partner gateway).
    los_backend: str = "demo"
    gateway_url: str = "https://partner-gateway-dev.dev.saas.rate.com/mcp/digital-mortgage-systems/tools"
    # Company the loans and borrowers belong to: "owning" (my.owning.com), with its Encompass company EID.
    gateway_company: str = "owning"
    gateway_company_eid: int = 5
    # Okta client-credentials token for the gateway. Credentials live in SSM.
    okta_token_url: str = "https://gr.oktapreview.com/oauth2/aus2aagfx9cSr6Aag0h8/v1/token"
    okta_scope: str = "api.all.digital-mortgage-systems-mcp"
    okta_client_id_param: str = ""
    okta_client_secret_param: str = ""
    # DynamoDB table that caches the Okta token across Lambda instances (optional).
    token_table: str = ""
    token_cache_key: str = "doc-intel-rate-gpt/okta/digital-mortgage-systems-mcp"

    # Where borrowers log in to upload documents after submitting.
    portal_url: str = "https://my.owning.com/login"

    @classmethod
    def from_env(cls) -> "Settings":
        defaults = cls()

        def env(name: str, default: str) -> str:
            return os.environ.get(f"RATE_GPT_{name}", default)

        return cls(
            modules=_csv(env("MODULES", ",".join(defaults.modules))),
            data_backend=env("DATA_BACKEND", defaults.data_backend),
            seed_demo_data=env("SEED_DEMO_DATA", "true").lower() == "true",
            applications_table=env("APPLICATIONS_TABLE", defaults.applications_table),
            host=env("HOST", defaults.host),
            port=int(env("PORT", str(defaults.port))),
            public_hosts=_csv(env("PUBLIC_HOSTS", "")),
            los_backend=env("LOS_BACKEND", defaults.los_backend),
            gateway_url=env("GATEWAY_URL", defaults.gateway_url),
            gateway_company=env("GATEWAY_COMPANY", defaults.gateway_company),
            gateway_company_eid=int(env("GATEWAY_COMPANY_EID", str(defaults.gateway_company_eid))),
            okta_token_url=env("OKTA_TOKEN_URL", defaults.okta_token_url),
            okta_scope=env("OKTA_SCOPE", defaults.okta_scope),
            okta_client_id_param=env("OKTA_CLIENT_ID_PARAM", defaults.okta_client_id_param),
            okta_client_secret_param=env("OKTA_CLIENT_SECRET_PARAM", defaults.okta_client_secret_param),
            token_table=env("TOKEN_TABLE", defaults.token_table),
            token_cache_key=env("TOKEN_CACHE_KEY", defaults.token_cache_key),
            portal_url=env("PORTAL_URL", defaults.portal_url),
        )
