Place reusable development scripts, validation helpers, and reproducible simulations here. Document assumptions; experiments do not become game rules automatically.

## Canonical commands
Developer setup and test commands are documented in the project `README.md` (Setup section). Run them from `new-game-project/`. The test command is `python -m pytest` with the project virtual environment active; test discovery and the `src/` import path are configured in `pyproject.toml` under `[tool.pytest.ini_options]`.

No extra tooling (linters, formatters, CI) is configured yet.
