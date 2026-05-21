import os

LOAN_OVERVIEW_TABLE = os.environ.get("LOAN_OVERVIEW_TABLE", "gpt-mcp-loan-overview-demo")
CLIENT_PROFILE_TABLE = os.environ.get("CLIENT_PROFILE_TABLE", "gpt-mcp-client-profile-demo")
LOAN_DOCUMENTS_BUCKET = os.environ.get("LOAN_DOCUMENTS_BUCKET", "gpt-mcp-loan-documents-demo")
LOAN_APPLICATION_TABLE = os.environ.get("LOAN_APPLICATION_TABLE", "gpt-mcp-loan-application-demo")

LOW_RISK_STATES = {"IL", "CA", "WA", "CO", "NY", "AZ", "NV", "OR"}
HIGH_RISK_INSURANCE_STATES = {"FL", "LA", "MS", "AL", "SC"}
