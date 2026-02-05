# HackApp - DXCare Integration Middleware

**Configuration-driven automation layer for EMR systems**

## Quick Start

```bash
# Install dependencies
pip install -r agent/requirements.txt
pip install -r middleware/requirements.txt
pip install -r mock_service/requirements.txt

# Start all services
./setup.sh

# Or start manually in 3 terminals:
python mock_service/app.py       # Terminal 1
python middleware/main.py         # Terminal 2
python agent/main.py              # Terminal 3
```

## Project Structure

```
hackapp/
├── agent/              Desktop agent (hotkeys + UI automation)
├── middleware/         Core brain (workflow engine + API)
├── connectors/         External service integrations
├── mock_service/       Mock external APIs
├── config/             Workflow and connector configurations
├── tests/              Integration tests
└── demo/               Demo materials
```

## Documentation

- [ARCHITECTURE.md](../ARCHITECTURE.md) - Complete system design
- [DXCARE_INTEGRATION_TECHNICAL.md](../DXCARE_INTEGRATION_TECHNICAL.md) - Technical feasibility
- [PROJECT_PLAN.md](../PROJECT_PLAN.md) - Phase-by-phase implementation plan
- [ANALYSIS_FROM_POWERPOINT.md](../ANALYSIS_FROM_POWERPOINT.md) - Requirements analysis

## Usage

1. Open DXCare (or simulator)
2. Click into a clinical field
3. Press **CTRL+ALT+V** to trigger voice summary workflow
4. Watch fields auto-fill with AI-generated content

## Configuration

Edit `config/workflows.yaml` to add new workflows. No code changes needed!

## License

MIT License
