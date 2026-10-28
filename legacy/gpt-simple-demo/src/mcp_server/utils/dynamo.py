import re
import boto3
from boto3.dynamodb.conditions import Key
from mcp_server.config import LOAN_OVERVIEW_TABLE, CLIENT_PROFILE_TABLE


def lookup_loan_dynamo(loan_identifier: str) -> dict | None:
    """
    Look up a loan record from DynamoDB by loan_id or guid.
    Tries a direct GetItem by loan_id first; if that misses, queries the guid GSI.
    Returns the item dict, or None if not found.
    """
    table = boto3.resource("dynamodb").Table(LOAN_OVERVIEW_TABLE)

    response = table.get_item(Key={"loan_id": loan_identifier})
    item = response.get("Item")
    if item:
        return item

    response = table.query(
        IndexName="guid-index",
        KeyConditionExpression=Key("guid").eq(loan_identifier),
        Limit=1,
    )
    items = response.get("Items", [])
    return items[0] if items else None


def lookup_client_profile(identifier: str) -> dict | None:
    """
    Look up a client profile from DynamoDB by borrower_id, loan_id, guid, or borrower name.
    Auto-detects the identifier type and tries the appropriate index.
    Returns the item dict, or None if not found.
    """
    table = boto3.resource("dynamodb").Table(CLIENT_PROFILE_TABLE)

    # UUID format → guid GSI
    if re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", identifier, re.IGNORECASE):
        resp = table.query(IndexName="guid-index", KeyConditionExpression=Key("guid").eq(identifier), Limit=1)
        items = resp.get("Items", [])
        return items[0] if items else None

    # All digits → loan_id GSI
    if identifier.isdigit():
        resp = table.query(IndexName="loan_id-index", KeyConditionExpression=Key("loan_id").eq(identifier), Limit=1)
        items = resp.get("Items", [])
        return items[0] if items else None

    # Contains a space → name lookup via name GSI
    if " " in identifier.strip():
        tokens = identifier.strip().split()
        first, last = tokens[0], tokens[-1]
        resp = table.query(
            IndexName="name-index",
            KeyConditionExpression=Key("borrower_last_name").eq(last) & Key("borrower_first_name").eq(first),
            Limit=1,
        )
        items = resp.get("Items", [])
        if items:
            return items[0]
        # Reversed order
        resp = table.query(
            IndexName="name-index",
            KeyConditionExpression=Key("borrower_last_name").eq(tokens[0]) & Key("borrower_first_name").eq(tokens[-1]),
            Limit=1,
        )
        items = resp.get("Items", [])
        if items:
            return items[0]
        # Last fallback: prefix match on first name
        resp = table.query(
            IndexName="name-index",
            KeyConditionExpression=Key("borrower_last_name").eq(tokens[0]) & Key("borrower_first_name").begins_with(tokens[1]),
            Limit=1,
        )
        items = resp.get("Items", [])
        return items[0] if items else None

    # Fall back to borrower_id direct lookup
    resp = table.get_item(Key={"borrower_id": identifier})
    return resp.get("Item")
