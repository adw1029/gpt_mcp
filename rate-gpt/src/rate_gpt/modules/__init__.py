"""Feature modules.

Each module is a package under rate_gpt.modules that exposes:

    def register(mcp: MCPServer, ctx: AppContext) -> None

and registers its tools there. Enable a module by adding its package name to
RATE_GPT_MODULES. Modules don't import each other; shared types live in
rate_gpt.domain and shared storage in rate_gpt.data.
"""
import importlib

from mcp.server.mcpserver import MCPServer

from rate_gpt.context import AppContext


def load_modules(mcp: MCPServer, ctx: AppContext, names: list[str]) -> None:
    for name in names:
        module = importlib.import_module(f"{__name__}.{name}")
        module.register(mcp, ctx)
