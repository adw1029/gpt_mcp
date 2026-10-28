"""Run the MCP server locally over Streamable HTTP at http://HOST:PORT/mcp."""
from mcp.server.transport_security import TransportSecuritySettings

from rate_gpt.config import Settings
from rate_gpt.server import build_server

_LOCAL_HOSTS = ["127.0.0.1:*", "localhost:*", "[::1]:*"]
_LOCAL_ORIGINS = ["http://127.0.0.1:*", "http://localhost:*", "http://[::1]:*"]


def main() -> None:
    settings = Settings.from_env()
    # The SDK only accepts localhost Host headers by default (DNS-rebinding
    # protection); a tunnel like ngrok arrives with its own domain.
    security = None
    if settings.public_hosts:
        security = TransportSecuritySettings(
            allowed_hosts=_LOCAL_HOSTS + settings.public_hosts,
            allowed_origins=_LOCAL_ORIGINS + [f"https://{h}" for h in settings.public_hosts],
        )
    build_server(settings).run(
        "streamable-http", host=settings.host, port=settings.port, transport_security=security
    )


if __name__ == "__main__":
    main()
