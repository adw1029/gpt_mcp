"""End-to-end tests: a real MCP client talking to the server in-process."""
import pytest
from mcp import Client

from rate_gpt.config import Settings
from rate_gpt.server import build_server

pytestmark = pytest.mark.anyio

COMPLETE_DETAILS = {
    "first_name": "Alex",
    "last_name": "Kim",
    "email": "alex.kim@example.com",
    "phone": "512-555-0188",
    "loan_purpose": "purchase",
    "loan_amount": 320000,
    "property_type": "condo",
    "occupancy": "primary_residence",
    "property_city": "Austin",
    "property_state": "TX",
    "property_zip": "78701",
    "property_value": 400000,
    "employer_name": "Acme Corp",
    "monthly_base_income": 10400,
}


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    async with Client(build_server(Settings())) as c:
        yield c


async def test_lists_enabled_module_tools(client):
    tools = {t.name for t in (await client.list_tools()).tools}
    assert tools == {
        "save_loan_application",
        "submit_loan_application",
        "get_application_status",
        "create_portal_account",
    }


async def test_modules_are_configurable():
    async with Client(build_server(Settings(modules=["status"]))) as c:
        tools = {t.name for t in (await c.list_tools()).tools}
    assert tools == {"get_application_status"}


async def test_seeded_status(client):
    result = await client.call_tool("get_application_status", {"application_id": "rg-100001"})
    status = result.structured_content
    assert not result.is_error
    assert status["borrower_name"] == "Jamie Torres"
    assert status["stage"] == "conditionally_approved"
    assert status["step"] == 4
    assert len(status["open_conditions"]) == 2


async def test_unknown_application_is_a_tool_error(client):
    result = await client.call_tool("get_application_status", {"application_id": "RG-NOPE"})
    assert result.is_error
    assert "No application found" in result.content[0].text


async def test_apply_over_several_turns_then_submit(client):
    first = await client.call_tool(
        "save_loan_application", {"details": {"first_name": "Alex", "loan_purpose": "purchase"}}
    )
    draft = first.structured_content
    app_id = draft["application_id"]
    assert draft["stage"] == "draft"
    assert "email" in draft["missing_fields"]
    assert not draft["ready_to_submit"]

    early = await client.call_tool("submit_loan_application", {"application_id": app_id})
    assert early.is_error
    assert "missing required fields" in early.content[0].text

    rest = {k: v for k, v in COMPLETE_DETAILS.items() if k not in ("first_name", "loan_purpose")}
    second = await client.call_tool("save_loan_application", {"application_id": app_id, "details": rest})
    assert second.structured_content["ready_to_submit"]
    assert second.structured_content["details"]["first_name"] == "Alex"  # kept from turn one

    submitted = await client.call_tool("submit_loan_application", {"application_id": app_id})
    assert submitted.structured_content["stage"] == "submitted"
    assert submitted.structured_content["upload_documents_url"] == "https://my.owning.com/login"
    assert first.structured_content["loan_id"] is None  # no loan until contact details are in
    loan_id = second.structured_content["loan_id"]
    assert loan_id
    assert submitted.structured_content["loan_id"] == loan_id

    status = await client.call_tool("get_application_status", {"application_id": app_id})
    assert status.structured_content["step"] == 1
    assert status.structured_content["loan_id"] == loan_id
    assert status.structured_content["recent_activity"][0]["note"] == "Application submitted."

    locked = await client.call_tool("save_loan_application", {"application_id": app_id, "details": {"phone": "1"}})
    assert locked.is_error


async def test_invalid_field_is_rejected(client):
    result = await client.call_tool("save_loan_application", {"details": {"property_state": "Texas"}})
    assert result.is_error


async def test_loan_amount_above_value_blocks_submit(client):
    details = {**COMPLETE_DETAILS, "loan_amount": 500000}
    draft = await client.call_tool("save_loan_application", {"details": details})
    result = await client.call_tool(
        "submit_loan_application", {"application_id": draft.structured_content["application_id"]}
    )
    assert result.is_error


async def test_next_step_asks_for_the_account_right_after_contact_details(client):
    first = await client.call_tool("save_loan_application", {"details": {"first_name": "Alex"}})
    assert "last_name, email, phone" in first.structured_content["next_step"]
    app_id = first.structured_content["application_id"]

    contact = {"last_name": "Kim", "email": "alex.kim@example.com", "phone": "512-555-0188"}
    second = await client.call_tool("save_loan_application", {"application_id": app_id, "details": contact})
    assert "create_portal_account" in second.structured_content["next_step"]
    assert second.structured_content["portal_account"] is None

    await client.call_tool("create_portal_account", {"application_id": app_id})
    third = await client.call_tool("save_loan_application", {"application_id": app_id, "details": COMPLETE_DETAILS})
    assert third.structured_content["portal_account"] == "created"
    assert "confirm" in third.structured_content["next_step"]

    submitted = await client.call_tool("submit_loan_application", {"application_id": app_id})
    assert "upload_documents_url" in submitted.structured_content["next_step"]


async def test_no_account_step_when_accounts_module_is_off():
    async with Client(build_server(Settings(modules=["applications"]))) as c:
        draft = await c.call_tool("save_loan_application", {"details": COMPLETE_DETAILS})
    assert "create_portal_account" not in draft.structured_content["next_step"]
