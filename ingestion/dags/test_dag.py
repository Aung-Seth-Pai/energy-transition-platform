"""
Placeholder DAG to verify Airflow is operational and parsing DAGs correctly.
Replace with real ingestion logic once infrastructure is confirmed stable.
"""

from datetime import datetime

from airflow.decorators import dag, task


@dag(
    dag_id="test_dag",
    description="Placeholder DAG — confirms Airflow is healthy.",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["placeholder"],
)
def test_dag():
    """Minimal DAG with a single no-op task."""

    @task
    def hello() -> None:
        """Logs a confirmation message."""
        from logger import get_logger

        log = get_logger(__name__)
        log.info("Airflow is operational. Replace this DAG with real ingestion logic.")

    hello()

test_dag()
