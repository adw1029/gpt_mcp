"""
MCP server exposing tools for GPT: get_user_info and retrieve_loan_info.
Designed to run on AWS Lambda behind API Gateway (Streamable HTTP).
"""
from awslabs.mcp_lambda_handler import MCPLambdaHandler

mcp = MCPLambdaHandler(name="gpt-app-mcp", version="1.0.0")


# In production, replace with real DB/API calls (e.g. DynamoDB, RDS, internal APIs)
def _get_user_from_store(user_id: str) -> dict:
    """Mock user store. Replace with your data source."""
    # Example in-memory data; use DynamoDB, RDS, or internal API in production
    users = {
        "user_001": {
            "user_id": "user_001",
            "name": "Jane Doe",
            "email": "jane.doe@example.com",
            "status": "active",
            "created_at": "2024-01-15",
        },
        "user_002": {
            "user_id": "user_002",
            "name": "John Smith",
            "email": "john.smith@example.com",
            "status": "active",
            "created_at": "2024-02-20",
        },
    }
    return users.get(user_id, {})


def _get_loan_from_store(loan_id: str) -> dict:
    """Mock loan store. Replace with your data source."""
    loans = {
        "loan_001": {
            "loan_id": "loan_001",
            "user_id": "user_001",
            "amount": 15000.00,
            "currency": "USD",
            "status": "active",
            "term_months": 36,
            "apr": 7.5,
            "remaining_balance": 12000.00,
        },
        "loan_002": {
            "loan_id": "loan_002",
            "user_id": "user_002",
            "amount": 25000.00,
            "currency": "USD",
            "status": "active",
            "term_months": 48,
            "apr": 6.9,
            "remaining_balance": 25000.00,
        },
    }
    return loans.get(loan_id, {})


@mcp.tool()
def get_user_info(user_id: str) -> str:
    """
    Retrieve information for a user by their user ID.
    Use this when the user asks about their profile, account, or identity.
    """
    import json

    data = _get_user_from_store(user_id)
    if not data:
        return json.dumps({"error": "User not found", "user_id": user_id})
    return json.dumps(data, indent=2)


@mcp.tool()
def retrieve_loan_info(loan_id: str) -> str:
    """
    Retrieve loan details by loan ID (balance, status, terms, APR).
    Use this when the user asks about a specific loan or their loan balance.
    """
    import json

    data = _get_loan_from_store(loan_id)
    if not data:
        return json.dumps({"error": "Loan not found", "loan_id": loan_id})
    return json.dumps(data, indent=2)


def lambda_handler(event, context):
    """AWS Lambda entrypoint. Wire this in your Lambda configuration."""
    return mcp.handle_request(event, context)
