# GPT MCP App – User & Loan Info Tools

Simple GPT app backend that exposes two MCP tools to GPT via a server running on AWS:

- **get_user_info** – Retrieve user profile by `user_id`
- **retrieve_loan_info** – Retrieve loan details by `loan_id`

The backend is an MCP server on **AWS Lambda** behind **API Gateway (HTTP API)**. GPT (OpenAI Responses API) talks to it using the **Streamable HTTP** MCP transport.

## Project layout

```
gpt_mcp/
├── src/
│   ├── handler.py          # Lambda entrypoint
│   ├── requirements.txt    # Lambda deps (for sam build)
│   └── mcp_server/
│       ├── __init__.py
│       └── server.py       # MCP server + get_user_info, retrieve_loan_info
├── template.yaml           # AWS SAM template (Lambda + HTTP API)
├── requirements.txt        # Local dev deps
└── README.md
```

## Run locally (optional)

Create a venv and install deps:

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

The tools use in-memory mock data in `server.py`. For local testing without Lambda, you can use the [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) with stdio or run the Lambda handler via a local Lambda runtime (e.g. [SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-local-invoke.html)).

## Deploy to AWS

1. **Install AWS SAM CLI**  
   [Install the AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html).

2. **Build and deploy**

   ```bash
   cd c:\Users\Andrew\Documents\gpt_mcp
   sam build
   sam deploy --guided
   ```

   Use the default stack name (or choose one), set **Stage** (e.g. `dev`), and accept defaults for the rest unless you need a different region or bucket.

3. **Get the MCP server URL**

   After deploy, SAM prints the stack outputs. Use the **McpApiUrl** value, e.g.:

   ```text
   https://<api-id>.execute-api.<region>.amazonaws.com/mcp
   ```

   If your HTTP API uses the `$default` stage, the URL might be:

   ```text
   https://<api-id>.execute-api.<region>.amazonaws.com/$default/mcp
   ```

   Use the URL that works when you call it from the OpenAI API (see below).

## Connect GPT to your MCP server

Use the **OpenAI Responses API** with the `mcp` tool type and your deployed URL as `server_url`. GPT will discover and call `get_user_info` and `retrieve_loan_info` from your backend.

### Example (Python)

```python
from openai import OpenAI

client = OpenAI()

resp = client.responses.create(
    model="gpt-4o",  # or another MCP-capable model
    tools=[
        {
            "type": "mcp",
            "server_label": "gpt-app",
            "server_description": "User and loan info for the GPT app.",
            "server_url": "https://<your-api-id>.execute-api.<region>.amazonaws.com/mcp",
            "require_approval": "never",
        }
    ],
    input="What is the balance for loan_001?",
)
print(resp.output_text)
```

### Example (curl)

```bash
curl https://api.openai.com/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "gpt-4o",
    "tools": [{
      "type": "mcp",
      "server_label": "gpt-app",
      "server_description": "User and loan info.",
      "server_url": "https://<your-api-id>.execute-api.<region>.amazonaws.com/mcp",
      "require_approval": "never"
    }],
    "input": "Get user info for user_001"
  }'
```

Replace `https://<your-api-id>.execute-api.<region>.amazonaws.com/mcp` with your **McpApiUrl** from the SAM deploy output.

- **ChatGPT / GPT in the OpenAI UI**  
  Remote MCP is used via the **Responses API** (or products built on it). In the ChatGPT UI you typically use Actions/connectors; for a *custom* backend like this you’d integrate via your own app that calls the Responses API with the `mcp` tool and this `server_url`.

- **Require approval**  
  Set `"require_approval": "always"` if you want to approve each tool call; use `"never"` for automatic calls (only if you trust the MCP server).

- **Auth**  
  If you add auth (e.g. API key or OAuth), pass it in the **authorization** field of the MCP tool config and protect your API Gateway (e.g. Lambda authorizer or API key).

## Tools

| Tool                | Description                          | Parameters   |
|---------------------|--------------------------------------|--------------|
| `get_user_info`     | Get user profile by user ID          | `user_id`    |
| `retrieve_loan_info`| Get loan details (balance, terms…)   | `loan_id`    |

Mock data in `src/mcp_server/server.py` includes `user_001`, `user_002`, `loan_001`, and `loan_002`. Replace `_get_user_from_store` and `_get_loan_from_store` with DynamoDB, RDS, or your internal APIs for production.

## Security and production

- **Auth**: Add API Gateway authorization (e.g. IAM, Lambda authorizer, or API key) and/or validate tokens inside the Lambda.
- **Data**: Do not rely on in-memory data in production; use a real store and restrict access by identity.
- **HTTPS**: API Gateway provides HTTPS; keep the MCP server URL on HTTPS when configuring GPT.

## References

- [OpenAI – MCP and Connectors (Responses API)](https://platform.openai.com/docs/guides/tools-remote-mcp)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [awslabs.mcp-lambda-handler (PyPI)](https://pypi.org/project/awslabs.mcp-lambda-handler/)
