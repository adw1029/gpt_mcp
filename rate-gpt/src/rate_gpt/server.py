from mcp.server.mcpserver import MCPServer

from rate_gpt.config import Settings
from rate_gpt.context import AppContext
from rate_gpt.modules import load_modules

INSTRUCTIONS = """\
You are Rate's mortgage assistant. You help borrowers apply for a mortgage and
check on their application. Always use the tools for anything about a specific
application; never guess loan details. Don't give rate or approval guarantees.

To apply: get the borrower's name, email and phone first, then create their
Rate portal account (never ask for a password), then continue the application. Tool responses
include next_step: follow it.
"""


def build_server(settings: Settings | None = None, ctx: AppContext | None = None) -> MCPServer:
    settings = settings or Settings.from_env()
    ctx = ctx or AppContext.from_settings(settings)
    mcp = MCPServer(name="rate-gpt", title="Rate", version="0.1.0", instructions=INSTRUCTIONS)
    load_modules(mcp, ctx, settings.modules)
    return mcp
