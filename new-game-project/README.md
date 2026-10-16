# New Game
Python-first local RPG prototype. Current design and combat notes are provisional.

## Setup
Requires Python 3.11 or newer. All commands below run from the `new-game-project/` directory (the folder containing `pyproject.toml`), not the repository root.

The first install needs internet access to download `pytest` and the `setuptools` build backend.

**macOS / Linux**
```bash
cd new-game-project
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m pytest
```

**Windows (PowerShell)**
```powershell
cd new-game-project
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest
```
In Command Prompt, activate with `.venv\Scripts\activate.bat` instead. If PowerShell refuses to run the activation script, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, or call the venv's Python directly: `.venv\Scripts\python -m pytest`.

Notes:
- Use `python -m pytest` (not bare `pytest`) so the tests run with the virtual environment's Python.
- The install is editable: changes under `src/game/` take effect without reinstalling. Reinstall only after editing `pyproject.toml`.
- If `python3 --version` / `py -3 --version` shows something older than 3.11, name a specific interpreter, e.g. `python3.11 -m venv .venv` or `py -3.11 -m venv .venv`.
- The smoke tests in `tests/test_smoke.py` check the environment itself; a failure there means setup is incomplete, and the message says what to fix.

## Play the combat prototype
With the virtual environment active, from `new-game-project/`:
```bash
python -m game.sim
```
Enter `a` to attack on your turn; the enemy attacks automatically on its turn. After each encounter, answer `y` to fight again or `n` to quit. Enter `q` at any prompt to quit. Combat rules and starting stats are PROVISIONAL prototype values, not approved balance.

## Project workflow
Read `AGENTS.md`, `docs/AGENT_PROTOCOL.md`, and `docs/WORKFLOW.md` before contributing. The human Game Director approves major design decisions. Work should be scoped, reviewed, and accepted before merging to `main`.
