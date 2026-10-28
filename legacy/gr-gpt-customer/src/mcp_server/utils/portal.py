import boto3
from mcp_server.config import BORROWER_PORTAL_TABLE


def lookup_borrower_portal(loan_id: str) -> dict | None:
    """
    Look up a borrower portal record from DynamoDB by loan_id.
    Returns the full item dict, or None if not found.
    """
    table = boto3.resource("dynamodb").Table(BORROWER_PORTAL_TABLE)
    response = table.get_item(Key={"loan_id": loan_id})
    return response.get("Item")
