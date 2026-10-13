# New Game
Python-first local RPG prototype. Current design and combat notes are provisional.

## Setup
Requires Python 3.11+.
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\Activate.ps1
python -m pip install -e ".[dev]"
pytest
```

## Project workflow
Read `AGENTS.md`, `docs/AGENT_PROTOCOL.md`, and `docs/WORKFLOW.md` before contributing. The human Game Director approves major design decisions. Work should be scoped, reviewed, and accepted before merging to `main`.
