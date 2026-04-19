---
trigger: always_on
---

# TransitionWatch: Core Development Rules

### 1. Monorepo & Dependency Management (STRICT)
- **Tooling:** This project strictly uses `uv` for dependency management with workspaces (`libs/core`, `ingestion`, `backend`, `frontend`, `nginx`).
- **Execution:** NEVER use `pip install`, `python -m`, or standard `pip`. 
- **Commands:** Always prefix execution commands with `uv run` (e.g., `uv run python script.py`).
- **Infrastructure:** Reference `pyproject.toml` at the root and within workspace folders, as well as Dockerfiles, for environment context.

### 2. Environment & Infrastructure (WSL/Docker)
- **WSL Context:** The project lives in a WSL (Windows Subsystem for Linux) environment.
- **Docker-First:** All services run via Docker. Do NOT assume a local Airflow/Postgres installation.
- **CLI Commands:** Use `docker exec -it <container_name> uv run ...` to execute commands inside the running environment.
- **Storage:** Use local filesystem emulation for GCS. Interact with volumes via `pathlib` and relative paths from the project root.

### 3. Python Standards & Strict Typing
- **Data Validation:** All classes must inherit from Pydantic V2 `BaseModel`.
- **Pydantic V2 Syntax:** - Use `.model_dump()` (NOT `.dict()`).
    - Use `.model_validate()` (NOT `.parse_obj()`).
    - Always use `Field` for default values and descriptions.
- **Logging:** NEVER use `print()`. Always import and use `get_logger` from `libs.core.logger`.

### 4. MVP Scope & Logic
- **Geographic Scope:** Worldwide and ASEAN aggregates only. 
- **Legacy Code:** Always reuse `ember_client.py`, `logging.py`, and existing DAGs. Do not rewrite existing logic; extend it.
- **Statelessness:** The backend (FastAPI) must remain stateless; it queries BigQuery but does not trigger Airflow DAGs directly.