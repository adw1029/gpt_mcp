import boto3
from boto3.dynamodb.conditions import Key
from mcp_server.config import LO_PIPELINE_TABLE


def lookup_lo_pipeline(lo_name: str) -> dict | None:
    """
    Look up a loan officer's pipeline record by name.
    Tries a direct GetItem by normalized lo_id first (e.g. "Jane Smith" → "jane-smith"),
    then falls back to the lo_name GSI for exact-match queries.
    Returns the full item dict, or None if not found.
    """
    table = boto3.resource("dynamodb").Table(LO_PIPELINE_TABLE)

    lo_id = lo_name.strip().lower().replace(" ", "-")
    resp = table.get_item(Key={"lo_id": lo_id})
    item = resp.get("Item")
    if item:
        return item

    resp = table.query(
        IndexName="lo_name-index",
        KeyConditionExpression=Key("lo_name").eq(lo_name.strip()),
        Limit=1,
    )
    items = resp.get("Items", [])
    return items[0] if items else None
