import os
import uuid
import urllib.parse
import boto3
from mcp_server.registry import mcp
from mcp_server.config import LOAN_DOCUMENTS_BUCKET
from mcp_server.utils.s3 import resolve_bucket_region


@mcp.tool()
def get_upload_url(loan_id: str) -> str:
    """
    Generate a secure upload link for a loan officer to submit a PDF document.

    Use this ONLY when the user wants to upload or submit a document, e.g.:
    - "I want to upload a document for loan 265561631"
    - "give me an upload link for loan 265561631"
    - "upload a title document for loan 265561631"
    - "upload an insurance document for loan 265561631"
    - "I need to submit a document for this loan"

    Returns a clickable https:// URL. After the loan officer confirms the
    upload is complete, call check_loan_approval with loan_id, document_type,
    and s3_key.

    Do NOT use this for:
    - Checking approval without uploading → use check_loan_approval directly
    - Viewing loan data → use get_loan_overview or get_loan_intelligence_report
    """
    bucket_region = resolve_bucket_region(LOAN_DOCUMENTS_BUCKET)
    s3 = boto3.client(
        "s3",
        region_name=bucket_region,
        endpoint_url=f"https://s3.{bucket_region}.amazonaws.com",
    )
    filename = f"loan-{loan_id}.pdf"
    s3_key = f"uploads/{loan_id}/{filename}"

    presigned = s3.generate_presigned_post(
        Bucket=LOAN_DOCUMENTS_BUCKET,
        Key=s3_key,
        Fields={"Content-Type": "application/pdf"},
        Conditions=[
            ["starts-with", "$Content-Type", ""],
            ["content-length-range", 1, 52428800],
        ],
        ExpiresIn=300,
    )

    session_id = str(uuid.uuid4())
    session_key = f"sessions/{loan_id}/{session_id}.json"
    import json
    session_data = {
        "action": presigned["url"],
        "fields": presigned["fields"],
        "loan_id": loan_id,
        "filename": filename,
        "s3_key": s3_key,
        "expires_in": 300,
        "callback_url": os.environ.get("MCP_API_URL", ""),
    }
    s3.put_object(
        Bucket=LOAN_DOCUMENTS_BUCKET,
        Key=session_key,
        Body=json.dumps(session_data).encode(),
        ContentType="application/json",
    )

    website_base = f"http://{LOAN_DOCUMENTS_BUCKET}.s3-website.{bucket_region}.amazonaws.com/upload.html"
    upload_link = f"{website_base}?session={urllib.parse.quote(session_key)}"

    return (
        f"## 📤 DOCUMENT UPLOAD — Loan #{loan_id}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"**🔗 Secure Upload Portal:** [→ Click here to upload your document]({upload_link})\n\n"
        "> ⏱️ This link expires in **5 minutes**. Open it now.\n\n"
        "---\n\n"
        "### 📋 Steps\n\n"
        "1. Click the link above to open the secure upload portal\n"
        "2. Drag and drop your PDF _(max 50 MB)_\n"
        "3. Click **Upload** to submit\n"
        "4. Return here and say **\"now check the approval\"**\n\n"
        "---\n\n"
        "| Detail | Value |\n"
        "|---|---|\n"
        f"| **Loan ID** | `{loan_id}` |\n"
        f"| **S3 Key** | `{s3_key}` |\n"
        f"| **Expires In** | 300 seconds |\n"
    )
