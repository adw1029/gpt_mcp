"""Borrower portal accounts: the login borrowers use to upload documents."""
from typing import Literal

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field

from rate_gpt.context import AppContext
from rate_gpt.domain.applications import LoanApplication
from rate_gpt.errors import as_tool_errors
from rate_gpt.modules.accounts.service import AccountService


class PortalAccount(BaseModel):
    application_id: str
    account: Literal["created", "existing"] = Field(
        description="created: a new login was set up. existing: the borrower already had one"
    )
    login_email: str
    login_url: str
    next_step: str = Field(description="What to tell the borrower. Follow it.")


def _account_view(app: LoanApplication, portal_url: str) -> PortalAccount:
    return PortalAccount(
        application_id=app.id,
        account=app.portal_account,
        login_email=app.details.email,
        login_url=portal_url,
        next_step=(
            "Tell the borrower their portal account is ready. To set their password, they go to "
            "login_url, click \"Forgot password\", and enter login_email. Then continue the application."
            if app.portal_account == "created"
            else "Tell the borrower they already have a portal account under login_email: they sign in "
            "at login_url, or use \"Forgot password\" there. Then continue the application."
        ),
    )


def register(mcp: MCPServer, ctx: AppContext) -> None:
    service = AccountService(ctx.applications, ctx.accounts)
    portal_url = ctx.settings.portal_url

    @mcp.tool(
        title="Create portal account",
        annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, open_world_hint=True),
    )
    def create_portal_account(application_id: str) -> PortalAccount:
        """
        Create the borrower's login for the Rate borrower portal, where they
        upload the documents their loan needs. Their email is the username.

        Call this as soon as the application has the borrower's name, email
        and phone, before asking anything else. Never ask the borrower for a
        password: they set their own on the portal. Follow next_step in the
        response, then continue the application with save_loan_application.
        """
        with as_tool_errors():
            return _account_view(service.create_account(application_id), portal_url)
