import logging
import secrets

from pydantic import SecretStr

from rate_gpt.data import ApplicationRepository
from rate_gpt.domain.applications import LoanApplication
from rate_gpt.errors import AppError, IntegrationError, NotFoundError
from rate_gpt.integrations import BorrowerAccounts

log = logging.getLogger(__name__)

REQUIRED_FOR_ACCOUNT = ["first_name", "last_name", "email", "phone"]


class AccountService:
    def __init__(self, repo: ApplicationRepository, accounts: BorrowerAccounts) -> None:
        self._repo = repo
        self._accounts = accounts

    def create_account(self, application_id: str) -> LoanApplication:
        """Set up the borrower's portal login from the contact details on their application.

        The login gets a random password that nobody ever sees; the borrower sets
        their own with "Forgot password". That keeps passwords out of the chat.
        """
        app = self._repo.get(application_id)
        if app is None:
            raise NotFoundError(f"No application found with ID {application_id}.")
        if app.portal_account is not None:
            return app
        if missing := [name for name in REQUIRED_FOR_ACCOUNT if getattr(app.details, name) is None]:
            raise AppError(f"Save the borrower's {', '.join(missing)} on the application first.")

        if app.portal_borrower_id is None:
            borrower = self._accounts.create_borrower(app.details)
            app.portal_borrower_id = borrower.id
            if borrower.already_existed:
                # They already have a portal login; creating another would fail.
                app.portal_account = "existing"
            self._repo.save(app)
            if app.portal_account is not None:
                return app

        try:
            self._accounts.create_login(app.details, app.portal_borrower_id, _throwaway_password())
        except IntegrationError as exc:
            log.warning("Couldn't create portal login for %s", app.id)
            raise IntegrationError("We couldn't create the login. Please try again.") from exc
        app.portal_account = "created"
        self._repo.save(app)
        return app


def _throwaway_password() -> SecretStr:
    # Random, with every character class Okta policies usually ask for. Never stored or shown.
    return SecretStr(secrets.token_urlsafe(24) + "Aa1!")
