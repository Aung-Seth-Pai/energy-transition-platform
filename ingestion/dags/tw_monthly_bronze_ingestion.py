from __future__ import annotations

import os
import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

import pendulum
from airflow.decorators import dag, task
from airflow.exceptions import AirflowSkipException

from logger import get_logger
from ingestion.ember.ember_client import EmberAPIClient

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
 
def _build_dir(path: Path) -> None:
    """Create nested directory structure if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)

def _resolve_date_window(logical_date: pendulum.DateTime, lookback_months: int = 6) -> tuple[str, str]:
    """
    Return (start_date_str, end_date_str) as 'YYYY-MM' strings.
    Uses Pendulum so month-boundary arithmetic is always correct.
    """
    start = logical_date.subtract(months=lookback_months)
    return start.strftime("%Y-%m"), logical_date.strftime("%Y-%m")
 
def _dispatch_endpoint(client: EmberAPIClient, endpoint_type: str, params: dict):
    """
    Single dispatch point for all Ember monthly endpoints.
    Raises ValueError for unknown types so failures are explicit.
    """
    dispatch = {
        "generation":          client.get_monthly_generation,
        "demand":              client.get_monthly_demand,
        "installed_capacity":  client.get_monthly_installed_capacity,
        "carbon_intensity":    client.get_monthly_carbon_intensity,
        "power_sector_emission": client.get_monthly_power_sector_emission,
    }
    if endpoint_type not in dispatch:
        raise ValueError(
            f"Unknown endpoint_type '{endpoint_type}'. "
            f"Valid options: {list(dispatch.keys())}"
        )
    return dispatch[endpoint_type](**params)
 
def _serialize_records(payload) -> list[dict]:
    """Serialize Pydantic v1 or v2 models to plain dicts."""
    try:
        return [rec.model_dump() for rec in payload.data]   # Pydantic v2
    except AttributeError:
        return [rec.dict() for rec in payload.data]          # Pydantic v1 — TODO: remove when fully on v2

def _write_partitioned(
    records: list[dict],
    payload_stats: dict,
    endpoint_type: str,
    bronze_zone: str,
    logical_date: pendulum.DateTime,
) -> dict[str, int]:
    """
    Partition records by date and write each partition to disk as JSON.
    Returns a summary dict {date_str: record_count} for logging / XCom.
 
    Isolated here so swapping to GCS only requires touching this function.
    """
    grouped: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        grouped[record["date"]].append(record)
 
    summary: dict[str, int] = {}
    for date_str, date_records in grouped.items():
        part_year, part_month = date_str.split("-")[:2]
        partition_path = (
            Path(bronze_zone)
            / "ember"
            / endpoint_type
            / f"year={part_year}"
            / f"month={part_month}"
        )
        _build_dir(partition_path)
 
        file_path = partition_path / "data.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "extracted_at": datetime.now().isoformat(),
                    "logical_date": logical_date.strftime("%Y-%m-%d"),
                    "stats": payload_stats,
                    "data": date_records,
                },
                f,
                indent=2,
            )
        summary[date_str] = len(date_records)
 
    return summary
 
# ---------------------------------------------------------------------------
# Core ingestion logic (dependency-injected client factory)
# ---------------------------------------------------------------------------

def _ingest(
    endpoint_type: str,
    logical_date: pendulum.DateTime,
    api_params: dict | None = None,
    client_factory: Callable[[], EmberAPIClient] | None = None,
) -> dict[str, int]:
    """
    Fetch one Ember monthly endpoint and land the data in the bronze zone.
 
    Parameters
    ----------
    endpoint_type : str
        One of the keys in _dispatch_endpoint's dispatch table.
    logical_date : pendulum.DateTime
        The DAG's scheduled execution date (injected by Airflow).
    api_params : dict, optional
        Extra params forwarded to the Ember API (e.g. entity_code, series).
    client_factory : callable, optional
        Returns an EmberAPIClient context manager. Defaults to the real client.
        Override in tests to inject a mock without patching os.getenv.
 
    Returns
    -------
    dict[str, int]
        Partition summary pushed to XCom automatically by TaskFlow.
    """
    bronze_zone = os.getenv("BRONZE_DIR", "/opt/data/bronze")
    api_key = os.getenv("EMBER_API_KEY")
    if not api_key:
        raise ValueError("EMBER_API_KEY environment variable is not set")
 
    if client_factory is None:
        client_factory = lambda: EmberAPIClient(api_key=api_key)  # noqa: E731
 
    start_date_str, end_date_str = _resolve_date_window(logical_date)
    logger.info(
        "Starting ingestion",
        extra={"endpoint": endpoint_type, "window": f"{start_date_str} → {end_date_str}"},
    )
 
    request_params = {
        "start_date": start_date_str,
        "end_date": end_date_str,
        **(api_params or {}),
    }
 
    with client_factory() as client:
        payload = _dispatch_endpoint(client, endpoint_type, request_params)
 
    records = _serialize_records(payload)
 
    if not records:
        logger.warning("No records returned for %s — skipping write", endpoint_type)
        raise AirflowSkipException(f"No data returned for {endpoint_type} ({start_date_str}→{end_date_str})")
 
    summary = _write_partitioned(
        records=records,
        payload_stats=payload.stats,
        endpoint_type=endpoint_type,
        bronze_zone=bronze_zone,
        logical_date=logical_date,
    )
 
    logger.info(
        "Ingestion complete",
        extra={"endpoint": endpoint_type, "partitions": len(summary), "total_records": len(records)},
    )
    return summary  # automatically pushed to XCom by TaskFlow
 
# ---------------------------------------------------------------------------
# DAG definition
# ---------------------------------------------------------------------------
 
default_args = {
    "owner": "tw_admin",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}
 
 
@dag(
    dag_id="tw_bronze_ingestion_monthly",
    default_args=default_args,
    description="Fetches monthly data from Ember API and lands it in local Bronze storage.",
    schedule="@monthly",
    start_date=datetime(2026, 4, 1),
    catchup=True,
    tags=["tw", "bronze", "energy"],
)
def tw_bronze_ingestion_monthly():
    """
    Medallion bronze-layer ingestion from the Ember Energy API.
 
    All five endpoints run in parallel. Each task:
      - uses a 6-month rolling lookback window to self-heal late data
      - writes Hive-partitioned JSON to the bronze zone (year=/month=)
      - pushes a partition summary dict to XCom for downstream tasks
    """
 
    @task(task_id="ingest_monthly_generation")
    def ingest_generation(logical_date=None) -> dict[str, int]:
        return _ingest("generation", logical_date)
 
    @task(task_id="ingest_monthly_demand")
    def ingest_demand(logical_date=None) -> dict[str, int]:
        return _ingest("demand", logical_date)
 
    @task(task_id="ingest_monthly_capacity")
    def ingest_capacity(logical_date=None) -> dict[str, int]:
        return _ingest("installed_capacity", logical_date)
 
    @task(task_id="ingest_monthly_carbon_intensity")
    def ingest_carbon_intensity(logical_date=None) -> dict[str, int]:
        return _ingest("carbon_intensity", logical_date)
 
    @task(task_id="ingest_monthly_power_sector_emission")
    def ingest_power_sector_emission(logical_date=None) -> dict[str, int]:
        return _ingest("power_sector_emission", logical_date)
 
    # All five tasks run in parallel — no explicit dependency chain needed.
    # TaskFlow infers independence automatically.
    ingest_generation()
    ingest_demand()
    ingest_capacity()
    ingest_carbon_intensity()
    ingest_power_sector_emission()
 
 
tw_bronze_ingestion_monthly()