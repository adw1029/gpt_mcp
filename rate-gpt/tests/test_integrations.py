"""Okta tokens, the DMS gateway client, LOS payload mapping, and the submit sequence. No network."""
import json

import httpx
import pytest

from rate_gpt.data.dynamo import DynamoApplicationRepository
from rate_gpt.data.memory import InMemoryApplicationRepository
from rate_gpt.domain.applications import ApplicationDetails, LoanApplication, Stage
from rate_gpt.errors import IntegrationError
from rate_gpt.integrations.dms_gateway import DmsGatewayClient
from rate_gpt.integrations.los import (
    GatewayLoanOriginationSystem,
    create_loan_payload,
    update_loan_payload,
)
from rate_gpt.integrations.okta import CachedToken, ClientCredentialsTokenProvider, DynamoTokenCache
from rate_gpt.modules.applications.service import ApplicationService

TOKEN_URL = "https://okta.test/oauth2/x/v1/token"
GATEWAY = "https://gateway.test/mcp/digital-mortgage-systems/tools"

PURCHASE = ApplicationDetails(
    first_name="Alex",
    last_name="Kim",
    email="alex.kim@example.com",
    phone="512.555.0188",
    loan_purpose="purchase",
    loan_amount=320000,
    property_type="condo",
    occupancy="primary_residence",
    property_city="Austin",
    property_state="TX",
    property_zip="78701",
    property_value=400000,
    employer_name="Acme Corp",
    monthly_base_income=10400,
)


class FakeTable:
    """Just enough of a boto3 DynamoDB Table for get_item/put_item."""

    def __init__(self, key: str) -> None:
        self.key = key
        self.items: dict[str, dict] = {}

    def get_item(self, Key):
        item = self.items.get(Key[self.key])
        return {"Item": item} if item else {}

    def put_item(self, Item):
        self.items[Item[self.key]] = Item


def gateway_reply(data=None, success=True, status=200):
    inner = {"success": success, **({"data": data} if data is not None else {})}
    return httpx.Response(
        status, json={"tool": "t", "result": json.dumps(inner), "success": success, "request_id": "req-1"}
    )


# --- Okta -----------------------------------------------------------------------------


def make_provider(handler, cache=None, clock=lambda: 1000.0, credentials=lambda: ("cid", "secret")):
    http = httpx.Client(transport=httpx.MockTransport(handler))
    return ClientCredentialsTokenProvider(TOKEN_URL, "api.all.test", credentials, http, cache, clock)


def test_token_request_shape_and_memory_cache():
    calls = []

    def handler(request: httpx.Request):
        calls.append(request)
        return httpx.Response(200, json={"access_token": "tok-1", "expires_in": 3600})

    provider = make_provider(handler)
    assert provider.token() == "tok-1"
    assert provider.token() == "tok-1"
    assert len(calls) == 1

    form = dict(httpx.QueryParams(calls[0].content.decode()))
    assert form == {"grant_type": "client_credentials", "scope": "api.all.test"}
    assert calls[0].headers["authorization"].startswith("Basic ")


def test_token_refreshes_near_expiry():
    now = [1000.0]
    tokens = iter(["tok-1", "tok-2"])
    provider = make_provider(
        lambda r: httpx.Response(200, json={"access_token": next(tokens), "expires_in": 300}),
        clock=lambda: now[0],
    )
    assert provider.token() == "tok-1"
    now[0] += 250  # inside the 60s refresh margin
    assert provider.token() == "tok-2"


def test_token_shared_through_dynamo_cache():
    table = FakeTable("name")
    cache = DynamoTokenCache(table, "k")
    first = make_provider(lambda r: httpx.Response(200, json={"access_token": "tok-1", "expires_in": 3600}), cache)
    assert first.token() == "tok-1"
    assert table.items["k"]["expiresAt"] == 4600

    def no_network(request):
        raise AssertionError("second instance should reuse the cached token")

    assert make_provider(no_network, cache).token() == "tok-1"


def test_token_cache_outage_falls_back_to_okta():
    class BrokenCache:
        def get(self):
            raise RuntimeError("dynamo down")

        def put(self, token: CachedToken):
            raise RuntimeError("dynamo down")

    provider = make_provider(
        lambda r: httpx.Response(200, json={"access_token": "tok-1", "expires_in": 3600}), BrokenCache()
    )
    assert provider.token() == "tok-1"


def test_okta_error_is_a_generic_integration_error():
    provider = make_provider(lambda r: httpx.Response(401, json={"error": "invalid_client"}))
    with pytest.raises(IntegrationError, match="couldn't reach the loan system"):
        provider.token()


# --- Gateway client ---------------------------------------------------------------------


def test_gateway_parses_nested_result_and_sends_bearer():
    seen = []

    def handler(request: httpx.Request):
        seen.append(request)
        return gateway_reply({"loanId": "guid-1"})

    client = DmsGatewayClient(GATEWAY + "/", lambda: "tok", httpx.Client(transport=httpx.MockTransport(handler)))
    result = client.call("create_loan", {"firstName": "Alex"})

    assert result == {"success": True, "data": {"loanId": "guid-1"}}
    assert str(seen[0].url) == f"{GATEWAY}/create_loan"
    assert seen[0].headers["authorization"] == "Bearer tok"
    assert json.loads(seen[0].content) == {"firstName": "Alex"}


def test_gateway_inner_failure_raises():
    client = DmsGatewayClient(
        GATEWAY, lambda: "tok", httpx.Client(transport=httpx.MockTransport(lambda r: gateway_reply(success=False)))
    )
    with pytest.raises(IntegrationError):
        client.call("finalize_loan", {})


def test_gateway_retries_once_on_401_with_fresh_token():
    current = ["stale"]
    seen = []

    def handler(request: httpx.Request):
        seen.append(request.headers["authorization"])
        return gateway_reply({}) if request.headers["authorization"] == "Bearer fresh" else httpx.Response(401)

    def invalidate():
        current[0] = "fresh"

    client = DmsGatewayClient(
        GATEWAY, lambda: current[0], httpx.Client(transport=httpx.MockTransport(handler)), on_unauthorized=invalidate
    )
    client.call("update_loan", {})
    assert seen == ["Bearer stale", "Bearer fresh"]


# --- Payload mapping ------------------------------------------------------------------------


def test_create_loan_payload():
    assert create_loan_payload(PURCHASE, "owning", 5) == {
        "firstName": "Alex",
        "lastName": "Kim",
        "loanPurposeType": "Purchase",
        "emailAddress": "alex.kim@example.com",
        "mobilePhone": "(512)-555-0188",
        "company-name": "owning",
        "companyEID": 5,
    }


def test_update_loan_payload_purchase():
    payload = update_loan_payload("guid-1", PURCHASE, "owning")
    assert payload["grLoanGuid"] == "guid-1"
    assert payload["purchasePriceAmount"] == 400000
    assert payload["downPaymentAmount"] == 80000
    assert payload["downPaymentPercent"] == 20
    assert payload["subjectProperty"] == {
        "propertyType": "Condominium",
        "occupancyType": "PrimaryResidence",
        "city": "Austin",
        "state": "TX",
        "zipCode": "78701",
    }
    assert payload["employment"][0] == {
        "id": "Employment/0",
        "employerName": "Acme Corp",
        "currentEmploymentIndicator": True,
        "basePayAmount": 10400,
        "owner": "Borrower",
    }


def test_update_loan_payload_refinance():
    refi = PURCHASE.model_copy(update={"loan_purpose": "refinance", "property_value": 650000})
    payload = update_loan_payload("guid-1", refi, "owning")
    assert "purchasePriceAmount" not in payload
    assert payload["subjectProperty"]["refinancePurposeType"] == "NoCashOut"
    assert payload["subjectProperty"]["appraisedValue"] == 650000


# --- Submit sequence ------------------------------------------------------------------------


class RecordingLos:
    def __init__(self, fail_on: str | None = None) -> None:
        self.calls: list[str] = []
        self.fail_on = fail_on

    def _step(self, name):
        self.calls.append(name)
        if name == self.fail_on:
            self.fail_on = None  # fail once, succeed on retry
            raise IntegrationError("boom")

    def create_loan(self, details):
        self._step("create")
        return "guid-1"

    def update_loan(self, loan_id, details):
        self._step("update")

    def finalize_loan(self, loan_id):
        self._step("finalize")


def draft_service(los):
    repo = InMemoryApplicationRepository()
    service = ApplicationService(repo, los)
    app = service.save_draft(PURCHASE)
    return service, repo, app.id


def test_submit_creates_updates_finalizes_in_order():
    los = RecordingLos()
    service, repo, app_id = draft_service(los)
    app = service.submit(app_id)
    assert los.calls == ["create", "update", "finalize"]
    assert app.stage is Stage.SUBMITTED
    assert repo.get(app_id).los_loan_id == "guid-1"


def test_submit_retry_reuses_loan_instead_of_creating_a_duplicate():
    los = RecordingLos(fail_on="update")
    service, repo, app_id = draft_service(los)
    with pytest.raises(IntegrationError):
        service.submit(app_id)
    assert repo.get(app_id).stage is Stage.DRAFT
    assert repo.get(app_id).los_loan_id == "guid-1"

    service.submit(app_id)
    assert los.calls == ["create", "update", "update", "finalize"]


def test_gateway_los_end_to_end_against_mock():
    seen = []

    def handler(request: httpx.Request):
        tool = request.url.path.rsplit("/", 1)[-1]
        seen.append((tool, json.loads(request.content)))
        return gateway_reply({"loanId": "guid-9"} if tool == "create_loan" else None)

    gateway = DmsGatewayClient(GATEWAY, lambda: "tok", httpx.Client(transport=httpx.MockTransport(handler)))
    service, _, app_id = draft_service(GatewayLoanOriginationSystem(gateway, "owning", 5))
    service.submit(app_id)

    assert [t for t, _ in seen] == ["create_loan", "update_loan", "finalize_loan"]
    assert seen[1][1]["grLoanGuid"] == "guid-9"
    assert seen[2][1] == {"gr-loan-guid": "guid-9"}


# --- DynamoDB repository --------------------------------------------------------------------


def test_dynamo_repository_round_trip():
    table = FakeTable("id")
    repo = DynamoApplicationRepository(table)
    app = LoanApplication(id="RG-ABC123", details=PURCHASE)
    repo.save(app)

    assert table.items["RG-ABC123"]["stage"] == "draft"
    assert repo.get(" rg-abc123 ") == app
    assert repo.get("RG-NOPE") is None


# --- Opening the loan during the draft --------------------------------------------------------

CONTACT = ApplicationDetails(
    first_name="Alex", last_name="Kim", email="alex.kim@example.com", phone="5125550188", loan_purpose="purchase"
)


def test_loan_opens_once_contact_fields_are_saved():
    los = RecordingLos()
    service = ApplicationService(InMemoryApplicationRepository(), los)

    app = service.save_draft(CONTACT.model_copy(update={"phone": None}))
    assert app.los_loan_id is None and los.calls == []

    app = service.save_draft(ApplicationDetails(phone="5125550188"), app.id)
    assert app.los_loan_id == "guid-1"

    service.save_draft(ApplicationDetails(property_city="Austin"), app.id)
    assert los.calls == ["create"]  # later saves reuse the loan

    service.save_draft(PURCHASE, app.id)
    service.submit(app.id)
    assert los.calls == ["create", "update", "finalize"]


def test_failed_open_keeps_the_answers_and_retries_on_submit():
    los = RecordingLos(fail_on="create")
    service, repo, app_id = draft_service(los)
    assert repo.get(app_id).los_loan_id is None
    assert repo.get(app_id).details == PURCHASE

    service.submit(app_id)
    assert los.calls == ["create", "create", "update", "finalize"]
    assert repo.get(app_id).los_loan_id == "guid-1"


def test_loans_and_borrowers_belong_to_owning_by_default():
    from rate_gpt.config import Settings

    assert (Settings().gateway_company, Settings().gateway_company_eid) == ("owning", 5)
