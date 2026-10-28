"""Loan application domain model, shared by every module that touches applications."""
from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    return datetime.now(UTC)


class Stage(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    UNDERWRITING = "underwriting"
    CONDITIONALLY_APPROVED = "conditionally_approved"
    CLEAR_TO_CLOSE = "clear_to_close"
    CLOSED = "closed"
    # Off-pipeline outcomes
    WITHDRAWN = "withdrawn"
    DENIED = "denied"


# The happy path a submitted application moves through, in order.
PIPELINE: list[Stage] = [
    Stage.SUBMITTED,
    Stage.PROCESSING,
    Stage.UNDERWRITING,
    Stage.CONDITIONALLY_APPROVED,
    Stage.CLEAR_TO_CLOSE,
    Stage.CLOSED,
]

TERMINAL_STAGES = {Stage.CLOSED, Stage.WITHDRAWN, Stage.DENIED}


class ApplicationDetails(BaseModel):
    """What the borrower tells us. Every field is optional so the app can be filled in over a conversation."""

    first_name: str | None = None
    last_name: str | None = None
    email: str | None = Field(None, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    phone: str | None = Field(None, pattern=r"^\D*(\d\D*){10}$", description="10-digit US mobile number")

    loan_purpose: Literal["purchase", "refinance", "cash_out_refinance"] | None = None
    loan_amount: float | None = Field(None, gt=0, description="Requested loan amount in USD")

    property_type: Literal["single_family", "condo", "townhouse"] | None = None
    occupancy: Literal["primary_residence", "second_home", "investment"] | None = None
    property_city: str | None = None
    property_state: str | None = Field(None, pattern=r"^[A-Z]{2}$", description="Two-letter US state code")
    property_zip: str | None = Field(None, pattern=r"^\d{5}$")
    property_value: float | None = Field(
        None, gt=0, description="Purchase price, or estimated value for a refinance, in USD"
    )

    employer_name: str | None = Field(None, description="Current employer; 'self-employed' is fine")
    monthly_base_income: float | None = Field(None, ge=0, description="Gross monthly base pay in USD")


REQUIRED_TO_SUBMIT: list[str] = list(ApplicationDetails.model_fields)
# What the LOS needs to open a loan; the rest is sent on submit.
REQUIRED_TO_CREATE_LOAN: list[str] = ["first_name", "last_name", "email", "phone", "loan_purpose"]


class StatusEvent(BaseModel):
    at: datetime
    stage: Stage
    note: str


class Condition(BaseModel):
    description: str
    status: Literal["open", "received", "cleared"] = "open"


class LoanOfficer(BaseModel):
    name: str
    email: str
    phone: str


class LoanApplication(BaseModel):
    id: str
    stage: Stage = Stage.DRAFT
    details: ApplicationDetails = Field(default_factory=ApplicationDetails)
    history: list[StatusEvent] = Field(default_factory=list)
    conditions: list[Condition] = Field(default_factory=list)
    loan_officer: LoanOfficer | None = None
    # Set once the loan exists in the loan origination system (GR loan GUID).
    los_loan_id: str | None = None
    # Borrower portal (MYA) account. The ID is saved as soon as MYA returns it, so a
    # retry after a failed login step reuses it. Status is set once the borrower can log in.
    portal_borrower_id: str | None = None
    portal_account: Literal["created", "existing"] | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    def missing_fields(self) -> list[str]:
        return [name for name in REQUIRED_TO_SUBMIT if getattr(self.details, name) is None]

    def move_to(self, stage: Stage, note: str) -> None:
        self.stage = stage
        self.updated_at = utcnow()
        self.history.append(StatusEvent(at=self.updated_at, stage=stage, note=note))
