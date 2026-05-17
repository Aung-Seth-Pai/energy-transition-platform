FROM python:3.12-slim

# git: required by dbt deps to fetch packages from dbt Hub
# libgomp1: required by duckdb
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /transform

RUN pip install --no-cache-dir \
    "dbt-core>=1.8.0" \
    "dbt-duckdb>=1.10.1"

# Copy only dependency manifests first.
# Docker layer cache: packages are only re-fetched when packages.yml changes.
COPY packages.yml .
COPY dbt_project.yml .
COPY profiles.yml .

# Bake dbt packages into the image at build time.
# This is the standard production pattern — no runtime deps installation needed.
# profiles-dir is needed so dbt can parse dbt_project.yml during deps.
RUN dbt deps --profiles-dir /transform

# Copy the rest of the project (models, tests, macros, etc.)
# This layer rebuilds on model changes but NOT on package changes.
COPY . .

ENTRYPOINT ["dbt"]
CMD ["--help"]