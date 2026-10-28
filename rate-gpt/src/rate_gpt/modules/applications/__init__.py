"""Loan applications: start, fill in over a conversation, and submit."""
from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field

from rate_gpt.context import AppContext
from rate_gpt.domain.applications import ApplicationDetails, LoanApplication, Stage
from rate_gpt.errors import as_tool_errors
from rate_gpt.modules.applications.service import ApplicationService

# The borrower's portal login needs these; the accounts module creates it.
ACCOUNT_FIELDS = ["first_name", "last_name", "email", "phone"]


class ApplicationDraft(BaseModel):
    application_id: str
    stage: Stage
    missing_fields: list[str]
    ready_to_submit: bool
    details: ApplicationDetails
    loan_id: str | None = Field(
        None, description="The loan's ID in the loan system, set once name, email, phone and loan purpose are saved"
    )
    upload_documents_url: str | None = Field(
        None, description="Set after submitting: where the borrower logs in to upload documents"
    )
    portal_account: str | None = Field(
        None, description="The borrower's portal login: created, existing, or null if not set up yet"
    )
    next_step: str = Field(description="What to do next in the conversation. Follow it.")


def _next_step(app: LoanApplication, missing: list[str], offer_account: bool) -> str:
    if app.stage is not Stage.DRAFT:
        return (
            "Give the borrower their loan_id and upload_documents_url, "
            "and tell them to log in there to upload documents."
        )
    if missing_contact := [name for name in ACCOUNT_FIELDS if getattr(app.details, name) is None]:
        return f"Ask for the borrower's {', '.join(missing_contact)} before anything else."
    if offer_account and app.portal_account is None:
        return (
            "Before continuing, offer to create the borrower's Rate portal account with "
            "create_portal_account: they'll log in there to upload documents. Don't ask for a "
            "password. If they already have an account, or don't want one now, continue."
        )
    if missing:
        return "Continue the application: ask for a few of the missing_fields at a time."
    return "Summarize the answers for the borrower and ask them to confirm before you submit."


def _draft_view(app: LoanApplication, portal_url: str, offer_account: bool) -> ApplicationDraft:
    missing = app.missing_fields()
    return ApplicationDraft(
        application_id=app.id,
        stage=app.stage,
        missing_fields=missing,
        ready_to_submit=app.stage is Stage.DRAFT and not missing,
        details=app.details,
        loan_id=app.los_loan_id,
        upload_documents_url=None if app.stage is Stage.DRAFT else portal_url,
        portal_account=app.portal_account,
        next_step=_next_step(app, missing, offer_account),
    )


def register(mcp: MCPServer, ctx: AppContext) -> None:
    service = ApplicationService(ctx.applications, ctx.los)
    portal_url = ctx.settings.portal_url
    offer_account = "accounts" in ctx.settings.modules

    @mcp.tool(
        title="Save loan application",
        annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, open_world_hint=True),
    )
    def save_loan_application(details: ApplicationDetails, application_id: str | None = None) -> ApplicationDraft:
        """
        Start a new mortgage application, or add details to a draft one.

        Omit application_id to start a new application; pass it to update an
        existing draft. Only send the fields the borrower has just given you,
        since fields you send replace what's already saved and fields you leave
        out are kept. The response lists the fields still missing: ask the
        borrower for a few at a time, conversationally. Don't invent values.

        Ask for name, email and phone first, and save them. Then have the
        borrower create their portal account before anything else. Once loan
        purpose is saved too, the loan is opened and loan_id is returned: tell
        the borrower their loan ID. Always follow next_step in the response.
        """
        with as_tool_errors():
            return _draft_view(service.save_draft(details, application_id), portal_url, offer_account)

    @mcp.tool(
        title="Submit loan application",
        annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, open_world_hint=True),
    )
    def submit_loan_application(application_id: str) -> ApplicationDraft:
        """
        Submit a completed draft application for processing.

        Only call this after the borrower has reviewed a summary of their
        answers and explicitly confirmed they want to submit. On success, give
        the borrower their loan_id and upload_documents_url: they log in there
        to upload the documents their loan needs.
        """
        with as_tool_errors():
            return _draft_view(service.submit(application_id), portal_url, offer_account)
