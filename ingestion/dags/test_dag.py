"""
Placeholder DAG to verify Airflow is operational and parsing DAGs correctly.
Replace with real ingestion logic once infrastructure is confirmed stable.
"""

from datetime import datetime

from airflow.decorators import dag, task
from ingestion.ember.ember_client import EmberAPIClient
from logger import get_logger

logger = get_logger(__name__)

@dag(
    dag_id="test_dag",
    description="DAG Smoketest — confirms Airflow is healthy.",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['bronze', 'SmokeTest'],
)
def ingest_ember_data():
    @task
    def test_client_init():
        client = EmberAPIClient(api_key="dummy_smoke_test_key")
        logger.info(f"Smoke Test: client initialized successfuly with base URL: {client.base_url}")
        return "Client OK"
    test_client_init()

# instantiate the DAG
ingest_ember_data()