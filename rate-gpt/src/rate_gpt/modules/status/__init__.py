"""Application status: where a borrower's application is and what happens next."""
from datetime import datetime

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations
from pydantic import BaseModel

from rate_gpt.context import AppContext
from rate_gpt.domain.applications import (
    PIPELINE,
    TERMINAL_STAGES,
    LoanApplication,
    LoanOfficer,
    Stage,
    StatusEvent,
)
from rate_gpt.errors import NotFoundError, as_tool_errors

_NEXT_STEP = {
    Stage.DRAFT: "Finish the remaining questions and submit the application.",
    Stage.SUBMITTED: "Log in to the borrower portal to upload the documents your loan needs. "
    "A processor will pick up the file within 1 business day.",
    Stage.PROCESSING: "Appraisal, title, and insurance are being ordered. This usually takes 3–5 business days.",
    Stage.UNDERWRITING: "An underwriter is reviewing the file. A decision usually takes 3–7 business days.",
    Stage.CONDITIONALLY_APPROVED: "Send in the open conditions below to move to clear to close.",
    Stage.CLEAR_TO_CLOSE: "Closing documents are being prepared. Closing is usually within 3–5 business days.",
    Stage.CLOSED: "The loan has closed. Congratulations!",
    Stage.WITHDRAWN: "This application was withdrawn. Contact your loan officer to reopen it.",
    Stage.DENIED: "This application was not approved. Your loan officer can walk through options.",
}


class ApplicationStatus(BaseModel):
    application_id: str
    borrower_name: str | None
    stage: Stage
    step: int | None
    total_steps: int
    is_final: bool
    next_step: str
    open_conditions: list[str]
    missing_fields: list[str]
    recent_activity: list[StatusEvent]
    loan_officer: LoanOfficer | None
    loan_id: str | None
    upload_documents_url: str | None
    last_updated: datetime


def _status_view(app: LoanApplication, portal_url: str) -> ApplicationStatus:
    names = [app.details.first_name, app.details.last_name]
    return ApplicationStatus(
        application_id=app.id,
        borrower_name=" ".join(n for n in names if n) or None,
        stage=app.stage,
        step=PIPELINE.index(app.stage) + 1 if app.stage in PIPELINE else None,
        total_steps=len(PIPELINE),
        is_final=app.stage in TERMINAL_STAGES,
        next_step=_NEXT_STEP[app.stage],
        open_conditions=[c.description for c in app.conditions if c.status == "open"],
        missing_fields=app.missing_fields() if app.stage is Stage.DRAFT else [],
        recent_activity=app.history[-5:][::-1],
        loan_officer=app.loan_officer,
        loan_id=app.los_loan_id,
        upload_documents_url=None if app.stage is Stage.DRAFT or app.stage in TERMINAL_STAGES else portal_url,
        last_updated=app.updated_at,
    )


def register(mcp: MCPServer, ctx: AppContext) -> None:
    repo = ctx.applications

    @mcp.tool(
        title="Get application status",
        annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False),
    )
    def get_application_status(application_id: str) -> ApplicationStatus:
        """
        Look up where a mortgage application is: its stage, what happens next,
        open conditions the borrower still owes, and recent activity.

        Use this whenever the borrower asks about their application or loan
        status. Lead with the stage and the next step; list any open conditions.
        """
        with as_tool_errors():
            app = repo.get(application_id)
            if app is None:
                raise NotFoundError(
                    f"No application found with ID {application_id}. "
                    "Ask the borrower to double-check it; IDs look like RG-100001."
                )
            return _status_view(app, ctx.settings.portal_url)
