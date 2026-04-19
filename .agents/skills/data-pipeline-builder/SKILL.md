## 1. Data Pipeline Builder (Ingestion Specialist)
- **Role:** Generates/modifies Airflow DAGs and extraction logic.
- **Standards:**
    - **Storage:** Use `BRONZE_ZONE` env var (default: `/tmp/tw-bronze`).
    - **Partitioning:** Path must follow `bronze/<source>/<endpoint>/year=YYYY/month=MM/data.json`.
    - **Client Reuse:** Strictly extend `ember_client.py` and use `libs/core` logger.
    - **Validation:** Force Pydantic V2 validation on all raw API responses.