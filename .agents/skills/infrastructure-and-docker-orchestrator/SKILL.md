## 4. Infrastructure & Docker Orchestrator (DevOps)
- **Role:** Manages the containerized environment on WSL.
- **Standards:**
    - **WSL Pathing:** Handle volume mounts carefully (WSL path to Container path).
    - **UV Workspaces:** Manage cross-package installs using `uv sync` and `uv run`.
    - **Docker Control:** Execute tasks via `docker exec -it <service> uv run ...`.
    - **Health Checks:** Ensure service dependencies (Postgres -> Airflow) are respected in Compose.