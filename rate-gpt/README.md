# rate-gpt

MCP server behind the Rate ChatGPT app. Borrowers can **apply for a mortgage**
and **check their application status** from inside ChatGPT.

## Run it locally

```bash
cd rate-gpt
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"

.venv/bin/rate-gpt            # serves http://127.0.0.1:8000/mcp
.venv/bin/pytest              # end-to-end tests through a real MCP client
```

To poke at the tools in a browser, run the MCP Inspector against the running server:

```bash
npx @modelcontextprotocol/inspector   # connect to http://127.0.0.1:8000/mcp (Streamable HTTP)
```

### Connect it to ChatGPT

ChatGPT has to reach the server over public HTTPS, so tunnel it:

```bash
ngrok http 8000
RATE_GPT_PUBLIC_HOSTS=<your-subdomain>.ngrok-free.app .venv/bin/rate-gpt
```

Then in ChatGPT, open **Settings → Apps & Connectors**, turn on developer mode,
and add a connector pointing at `https://<your-subdomain>.ngrok-free.app/mcp`.

The memory store is seeded with demo applications. `RG-100001` (Jamie Torres)
is conditionally approved with open conditions, and `RG-100002` (Priya Shah)
is in underwriting. All state resets when the server restarts.

## Tools

| Tool | Module | What it does |
|---|---|---|
| `save_loan_application` | applications | Start a draft or merge in more fields; returns what's still missing |
| `submit_loan_application` | applications | Validate and submit a complete draft |
| `get_application_status` | status | Stage, step N of 6, next step, open conditions, recent activity, LO contact |

Tools return typed structured output (`structuredContent`). That keeps the
model grounded, and it's what a ChatGPT UI widget would render later.

## Layout

```
src/rate_gpt/
├── __main__.py        # local entrypoint (Streamable HTTP)
├── server.py          # build_server(): creates MCPServer, loads enabled modules
├── config.py          # Settings from env (see .env.example)
├── context.py         # AppContext: shared dependencies passed to every module
├── errors.py          # AppError family -> MCP tool errors
├── domain/            # shared models (LoanApplication, Stage, ...)
├── data/              # repository protocols + backends (memory today)
│   └── seed/          # demo records
└── modules/           # one package per feature; each exposes register(mcp, ctx)
    ├── applications/
    └── status/
```

The rules that keep this scalable:

- **Modules are the unit of growth.** A module only registers tools against
  `AppContext`. Modules never import each other.
- **Tools stay thin.** Business rules live in services and domain models, so the
  same logic can sit behind another transport or a REST API later.
- **Storage hides behind protocols.** Modules depend on `ApplicationRepository`,
  not on DynamoDB or memory, and the backend is chosen in `data/__init__.py`.

## Adding a module (e.g. credit)

1. Create `src/rate_gpt/modules/credit/__init__.py` with `register(mcp, ctx)` and its tools.
2. If it needs new data, add a repository protocol and backend in `data/`, then wire it into `AppContext`.
3. Add `credit` to `RATE_GPT_MODULES`.
4. Add tests in `tests/`.

## Not done yet

- **Auth / borrower identity.** Right now anyone with an application ID can see its status. This needs to be OAuth before anything goes beyond a demo.
- **Persistent storage.** Still needed: a DynamoDB (or LOS-backed) repository.
- **Deployment.** The Lambda/SAM setup is pending the MCP setup details.
- **ChatGPT UI widgets.** These would use the MCP Apps extension, `mcp.server.apps`.
