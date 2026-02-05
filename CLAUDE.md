# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HackApp is a configuration-driven middleware system that lets clinicians trigger AI-powered clinical workflows via hotkeys. When a clinician selects text in an EMR (DXCare) and presses a hotkey, the system captures the text, routes it through a workflow to an external service, and automatically populates EMR fields with the response (e.g., diagnosis summary and ICD-10 code).

This is a hackathon prototype. Prioritize getting things working over production-grade polish.

## Running the System

All commands assume the project root as working directory. Each service needs its own terminal, and they must start in this order:

```bash
# 1. Install dependencies (once)
pip install -r hackapp/agent/requirements.txt
pip install -r hackapp/middleware/requirements.txt
pip install -r hackapp/mock_service/requirements.txt

# 2. Terminal 1 — Mock external service (port 5001)
cd hackapp && python3 mock_service/app.py

# 3. Terminal 2 — Middleware API (port 5000)
cd hackapp && python3 middleware/main.py

# 4. Terminal 3 — Desktop agent (hotkey listener)
cd hackapp && python3 agent/main.py
```

Alternatively, `setup.sh` starts all three in background with logs to `./logs/`.

### Health checks (curl)

```bash
curl http://localhost:5001/health                          # mock service
curl http://localhost:5000/api/health                     # middleware
curl -X POST http://localhost:5000/api/trigger \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer hackathon_demo_token" \
  -d '{"hotkey":"CTRL+ALT+V","context":{"selected_text":"Patient has pneumonia with cough and fever"}}'
```

### Running the config test

```bash
cd hackapp && python3 tests/test_config.py
```

This is the only test file. It verifies that YAML configs load and parse correctly via Pydantic models.

## Architecture

Three layers, each in its own directory under `hackapp/`:

```
Agent (desktop client)  →  Middleware (FastAPI)  →  External services (or mock)
agent/                      middleware/               mock_service/
```

**Agent** (`agent/`): Runs on the clinician's desktop. Listens for global hotkeys via `pynput`, captures clipboard/selected text, POSTs to the middleware, and uses `pyautogui` to type the response into EMR fields. No business logic lives here.

**Middleware** (`middleware/`): The core brain. A FastAPI server that:
- Loads workflow and connector definitions from YAML (`config/`)
- Matches an incoming hotkey to a workflow
- Validates input, renders a Jinja2 request template, calls the external connector via REST
- Extracts response fields using JSONPath, validates them (including ICD-10 format), and returns insertion instructions to the agent
- All orchestration happens in `workflow_engine.py`; the other modules (`connector.py`, `transformers.py`, `validators.py`, `audit.py`, `config_loader.py`) are single-responsibility components consumed by it.

**Mock service** (`mock_service/`): A Flask app simulating external AI services. Uses keyword matching against clinical text to return canned diagnosis summaries and ICD-10 codes. Only needed for local development/demo — swap `connectors.yaml` URLs to point at real services for production.

## Configuration-Driven Workflows

New workflows and connectors are defined entirely in YAML — no code changes needed:

- `config/workflows.yaml` — defines hotkeys, input sources, request templates (Jinja2), response field mappings (JSONPath), output insertion instructions, and security rules (field whitelists).
- `config/connectors.yaml` — defines external service endpoints, auth, retry policies.
- `config/icd10_mini.yaml` — a 20-code ICD-10 catalog used for validation.

The middleware's `config_loader.py` parses these into Pydantic models defined in `models.py`. The `WorkflowEngine` in `workflow_engine.py` is the only consumer of these configs at runtime.

## Key Conventions

- **PYTHONPATH**: When running any module directly (`python3 middleware/main.py`), the working directory must be `hackapp/` so that intra-package imports (e.g., `from middleware.models import ...`) resolve correctly.
- **Auth token**: The agent↔middleware bearer token is `hackathon_demo_token`, set via `MIDDLEWARE_TOKEN` env var (defaults to that value). It is also hardcoded in `agent/config.py`.
- **Ports**: Mock service = 5001, Middleware = 5000. The agent connects to middleware; middleware connects to the mock service (or real external service).
- **Audit logging**: `audit.py` deliberately never logs clinical text or patient data — only workflow metadata, status, and timing. Don't change this behavior.
- **Input text flow**: The agent reads selected text via clipboard (`Ctrl+C` must happen before the hotkey). `context.selected_text` in the trigger payload is actually the clipboard content.

## Adding a New Workflow

1. Add a connector entry to `config/connectors.yaml` if the workflow talks to a new service.
2. Add a workflow entry to `config/workflows.yaml`: pick a hotkey, define input validation, a Jinja2 request template, JSONPath response mappings, output instructions, and a field whitelist.
3. Register the hotkey in `agent/config.py` under `HOTKEYS` so the agent listens for it.
4. If testing locally, add a matching endpoint to `mock_service/app.py` and keyword patterns to `mock_service/data.py`.

## Ports and Service Dependencies

| Service | Port | Depends on |
|---|---|---|
| Mock service | 5001 | — |
| Middleware | 5000 | Mock service (or real external APIs) |
| Agent | — | Middleware |

Start order: mock → middleware → agent.
