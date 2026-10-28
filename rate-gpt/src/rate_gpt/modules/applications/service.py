import logging
import secrets

from rate_gpt.data import ApplicationRepository
from rate_gpt.domain.applications import (
    REQUIRED_TO_CREATE_LOAN,
    ApplicationDetails,
    LoanApplication,
    Stage,
    utcnow,
)
from rate_gpt.errors import AppError, IntegrationError, InvalidStateError, NotFoundError
from rate_gpt.integrations import LoanOriginationSystem

log = logging.getLogger(__name__)


class ApplicationService:
    def __init__(self, repo: ApplicationRepository, los: LoanOriginationSystem) -> None:
        self._repo = repo
        self._los = los

    def save_draft(self, details: ApplicationDetails, application_id: str | None = None) -> LoanApplication:
        """Create a draft, or merge non-empty fields into an existing draft."""
        if application_id is None:
            app = LoanApplication(id=self._new_id())
        else:
            app = self.get(application_id)
            if app.stage is not Stage.DRAFT:
                raise InvalidStateError(
                    f"Application {app.id} was already submitted and can't be edited here. "
                    "The borrower should contact their loan officer to make changes."
                )

        app.details = app.details.model_copy(update=details.model_dump(exclude_none=True))
        app.updated_at = utcnow()
        self._repo.save(app)
        self._open_loan_when_ready(app)
        return app

    def submit(self, application_id: str) -> LoanApplication:
        app = self.get(application_id)
        if app.stage is not Stage.DRAFT:
            raise InvalidStateError(f"Application {app.id} was already submitted.")
        if missing := app.missing_fields():
            raise AppError(f"Application {app.id} is missing required fields: {', '.join(missing)}.")
        if app.details.loan_amount > app.details.property_value:
            raise AppError("Loan amount can't be more than the property value.")

        # Normally the loan was opened during the draft; this covers a create that failed then.
        if app.los_loan_id is None:
            app.los_loan_id = self._los.create_loan(app.details)
            self._repo.save(app)
        self._los.update_loan(app.los_loan_id, app.details)
        self._los.finalize_loan(app.los_loan_id)

        app.move_to(Stage.SUBMITTED, "Application submitted.")
        self._repo.save(app)
        return app

    def _open_loan_when_ready(self, app: LoanApplication) -> None:
        """Open the loan in the LOS once the draft has what create_loan needs.

        The loan ID is saved right away, so later saves and submit reuse the
        same loan instead of creating a duplicate. A failure here doesn't lose
        the borrower's answers: the next save, or submit, tries again.
        """
        if app.los_loan_id is not None:
            return
        if any(getattr(app.details, name) is None for name in REQUIRED_TO_CREATE_LOAN):
            return
        try:
            app.los_loan_id = self._los.create_loan(app.details)
        except IntegrationError:
            log.warning("Couldn't open loan for %s yet; will retry on the next save or submit", app.id)
            return
        self._repo.save(app)

    def get(self, application_id: str) -> LoanApplication:
        app = self._repo.get(application_id)
        if app is None:
            raise NotFoundError(f"No application found with ID {application_id}.")
        return app

    def _new_id(self) -> str:
        while True:
            candidate = f"RG-{secrets.token_hex(3).upper()}"
            if self._repo.get(candidate) is None:
                return candidate
