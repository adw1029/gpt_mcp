"""Borrower portal (MYA) accounts: the login borrowers use at my.owning.com to upload documents.

An account is two gateway calls: create_borrower_entity makes the MYA borrower,
then create_okta_user makes their login, linked by the MYA borrower ID.
"""
import uuid
from typing import Any, NamedTuple, Protocol

from pydantic import SecretStr

from rate_gpt.domain.applications import ApplicationDetails
from rate_gpt.integrations.dms_gateway import DmsGatewayClient
from rate_gpt.integrations.los import format_phone


class PortalBorrower(NamedTuple):
    id: str
    already_existed: bool


class BorrowerAccounts(Protocol):
    def create_borrower(self, details: ApplicationDetails) -> PortalBorrower: ...

    def create_login(self, details: ApplicationDetails, borrower_id: str, password: SecretStr) -> None: ...


class DemoBorrowerAccounts:
    """Stand-in for local runs and tests: hands out fake IDs, sends nothing anywhere."""

    def create_borrower(self, details: ApplicationDetails) -> PortalBorrower:
        return PortalBorrower(str(uuid.uuid4()), already_existed=False)

    def create_login(self, details: ApplicationDetails, borrower_id: str, password: SecretStr) -> None:
        pass


class GatewayBorrowerAccounts:
    def __init__(self, gateway: DmsGatewayClient, company: str) -> None:
        self._gateway = gateway
        self._company = company

    def create_borrower(self, details: ApplicationDetails) -> PortalBorrower:
        result = self._gateway.call("create_borrower_entity", create_borrower_payload(details, self._company))
        data = result["data"]
        return PortalBorrower(data["id"], already_existed=bool(data.get("already-exists")))

    def create_login(self, details: ApplicationDetails, borrower_id: str, password: SecretStr) -> None:
        self._gateway.call("create_okta_user", create_login_payload(details, borrower_id, password))


def create_borrower_payload(d: ApplicationDetails, company: str) -> dict[str, Any]:
    return {
        "email-address": {"primary": d.email},
        "identifier": {"okta-id": None},
        "name": {"first": d.first_name, "last": d.last_name},
        "phone": {"home": format_phone(d.phone)},
        "language-preference": "en",
        "company-name": company,
    }


def create_login_payload(d: ApplicationDetails, borrower_id: str, password: SecretStr) -> dict[str, Any]:
    return {
        "profile": {
            "firstName": d.first_name,
            "lastName": d.last_name,
            "email": d.email,
            "login": d.email,
            "mobilePhone": format_phone(d.phone),
            "borrowerID": borrower_id,
        },
        "credentials": {"password": {"value": password.get_secret_value()}},
    }
