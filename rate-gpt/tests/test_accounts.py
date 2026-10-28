"""Borrower portal accounts: payloads, the two-step create, and keeping the password out of storage. No network."""
import json

import httpx
import pytest
from mcp import Client
from pydantic import SecretStr

from rate_gpt.config import Settings
from rate_gpt.context import AppContext
from rate_gpt.data.dynamo import DynamoApplicationRepository
from rate_gpt.data.memory import InMemoryApplicationRepository
from rate_gpt.domain.applications import ApplicationDetails, LoanApplication
from rate_gpt.errors import AppError, IntegrationError
from rate_gpt.integrations.accounts import (
    GatewayBorrowerAccounts,
    PortalBorrower,
    create_borrower_payload,
    create_login_payload,
)
from rate_gpt.integrations.dms_gateway import DmsGatewayClient
from rate_gpt.integrations.los import DemoLoanOriginationSystem
from rate_gpt.modules.accounts.service import AccountService
from rate_gpt.server import build_server

GATEWAY = "https://gateway.test/mcp/digital-mortgage-systems/tools"
PASSWORD = SecretStr("Sample-Pass-123")

CONTACT = ApplicationDetails(
    first_name="Alex", last_name="Kim", email="alex.kim@example.com", phone="5125550188", loan_purpose="purchase"
)


def test_create_borrower_payload():
    assert create_borrower_payload(CONTACT, "owning") == {
        "email-address": {"primary": "alex.kim@example.com"},
        "identifier": {"okta-id": None},
        "name": {"first": "Alex", "last": "Kim"},
        "phone": {"home": "(512)-555-0188"},
        "language-preference": "en",
        "company-name": "owning",
    }


def test_create_login_payload():
    assert create_login_payload(CONTACT, "mya-1", PASSWORD) == {
        "profile": {
            "firstName": "Alex",
            "lastName": "Kim",
            "email": "alex.kim@example.com",
            "login": "alex.kim@example.com",
            "mobilePhone": "(512)-555-0188",
            "borrowerID": "mya-1",
        },
        "credentials": {"password": {"value": "Sample-Pass-123"}},
    }


class RecordingAccounts:
    def __init__(self, existing: bool = False, fail_login: bool = False) -> None:
        self.calls: list[str] = []
        self.existing = existing
        self.fail_login = fail_login

    def create_borrower(self, details):
        self.calls.append("borrower")
        return PortalBorrower("mya-1", already_existed=self.existing)

    def create_login(self, details, borrower_id, password):
        self.calls.append(f"login:{borrower_id}")
        if self.fail_login:
            self.fail_login = False  # fail once, succeed on retry
            raise IntegrationError("boom")


def saved_app(repo, details=CONTACT):
    app = LoanApplication(id="RG-ABC123", details=details)
    repo.save(app)
    return app.id


def test_new_borrower_gets_entity_then_login():
    repo, accounts = InMemoryApplicationRepository(), RecordingAccounts()
    app = AccountService(repo, accounts).create_account(saved_app(repo))
    assert accounts.calls == ["borrower", "login:mya-1"]
    assert app.portal_account == "created"
    assert repo.get(app.id).portal_borrower_id == "mya-1"


def test_existing_borrower_skips_the_login():
    repo, accounts = InMemoryApplicationRepository(), RecordingAccounts(existing=True)
    app = AccountService(repo, accounts).create_account(saved_app(repo))
    assert accounts.calls == ["borrower"]
    assert app.portal_account == "existing"


def test_failed_login_keeps_the_borrower_and_retry_reuses_it():
    repo, accounts = InMemoryApplicationRepository(), RecordingAccounts(fail_login=True)
    service = AccountService(repo, accounts)
    app_id = saved_app(repo)
    with pytest.raises(IntegrationError, match="couldn't create the login"):
        service.create_account(app_id)
    assert repo.get(app_id).portal_borrower_id == "mya-1"
    assert repo.get(app_id).portal_account is None

    service.create_account(app_id)
    service.create_account(app_id)  # already set up: no more calls
    assert accounts.calls == ["borrower", "login:mya-1", "login:mya-1"]


def test_needs_contact_details_first():
    repo, accounts = InMemoryApplicationRepository(), RecordingAccounts()
    app_id = saved_app(repo, ApplicationDetails(first_name="Alex"))
    with pytest.raises(AppError, match="last_name, email, phone"):
        AccountService(repo, accounts).create_account(app_id)
    assert accounts.calls == []


def test_generated_password_reaches_the_gateway_but_is_never_stored():
    table = {}

    class Table:
        def put_item(self, Item):
            table[Item["id"]] = Item

        def get_item(self, Key):
            return {"Item": table[Key["id"]]} if Key["id"] in table else {}

    sent = []

    class Accounts(RecordingAccounts):
        def create_login(self, details, borrower_id, password):
            sent.append(password.get_secret_value())

    repo = DynamoApplicationRepository(Table())
    AccountService(repo, Accounts()).create_account(saved_app(repo))
    assert len(sent[0]) >= 30
    assert sent[0] not in json.dumps(table)


def test_gateway_accounts_against_mock():
    seen = []

    def handler(request: httpx.Request):
        tool = request.url.path.rsplit("/", 1)[-1]
        seen.append((tool, json.loads(request.content)))
        inner = {"success": True, "data": {"id": "mya-9", "already-exists": False}}
        return httpx.Response(200, json={"tool": tool, "result": json.dumps(inner), "success": True})

    gateway = DmsGatewayClient(GATEWAY, lambda: "tok", httpx.Client(transport=httpx.MockTransport(handler)))
    repo = InMemoryApplicationRepository()
    AccountService(repo, GatewayBorrowerAccounts(gateway, "owning")).create_account(saved_app(repo))

    assert [t for t, _ in seen] == ["create_borrower_entity", "create_okta_user"]
    assert seen[1][1]["profile"]["borrowerID"] == "mya-9"


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_tool_end_to_end():
    from rate_gpt.integrations.accounts import DemoBorrowerAccounts

    settings = Settings()
    repo = InMemoryApplicationRepository()
    ctx = AppContext(settings, repo, DemoLoanOriginationSystem(), DemoBorrowerAccounts())
    app_id = saved_app(repo)
    async with Client(build_server(settings, ctx)) as client:
        tool = next(t for t in (await client.list_tools()).tools if t.name == "create_portal_account")
        assert set(tool.input_schema["properties"]) == {"application_id"}
        result = await client.call_tool("create_portal_account", {"application_id": app_id})
    assert not result.is_error
    account = result.structured_content
    assert "Forgot password" in account.pop("next_step")
    assert account == {
        "application_id": app_id,
        "account": "created",
        "login_email": "alex.kim@example.com",
        "login_url": "https://my.owning.com/login",
    }
