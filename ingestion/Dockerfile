FROM apache/airflow:2.11.2-python3.12
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /opt/airflow

# 1. Copy configurations and readmes
COPY --chown=airflow:root pyproject.toml uv.lock ./
COPY --chown=airflow:root ingestion/pyproject.toml ingestion/README.md ./ingestion/
COPY --chown=airflow:root libs/logger/pyproject.toml libs/logger/README.md ./libs/logger/

# 2. Copy the source code for the workspace packages
COPY --chown=airflow:root libs/logger/src ./libs/logger/src
COPY --chown=airflow:root ingestion/src ./ingestion/src/

# 3. Install workspace packages into the active environment
RUN uv pip install --no-cache -e libs/logger/ -e ingestion/

# 4. Copy DAGs (These don't need to be built by uv, so they can stay at the bottom)
COPY --chown=airflow:root ingestion/dags ./dags/

USER airflow