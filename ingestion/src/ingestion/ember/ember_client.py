import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from logger import get_logger

from pydantic import BaseModel
from typing import List, Optional, Dict, Any, TypeVar, Generic

logger = get_logger(__name__)

class EmberBaseRecord(BaseModel):
    """
    These are base fields returned in the JSON payload across all Ember datasets.
    """
    entity: str
    entity_code: Optional[str] = None
    is_aggregate_entity: bool
    date: str  # Kept as string to handle both "YYYY" and "YYYY-MM"

class EmberGenerationRecord(EmberBaseRecord):
    """
    payload schema for /electricity-generation endpoints.
    """
    series: str
    is_aggregate_series: bool
    generation_twh: Optional[float] = None
    share_of_generation_pct: Optional[float] = None

class EmberMonthlyDemandRecord(EmberBaseRecord):
    """
    payload schema for monthly /electricity-demand endpoints.
    """
    demand_twh: Optional[float] = None

class EmberYearlyDemandRecord(EmberMonthlyDemandRecord):
    """
    payload schema for yearly /electricity-demand endpoints.
    """
    demand_mwh_per_capita: Optional[float] = None

class EmberCarbonIntensityRecord(EmberBaseRecord):
    """
    payload schema for /carbon-intensity endpoints.
    """
    emissions_intensity_gco2_per_kwh: Optional[float] = None

class EmberPowerSectorEmissionRecord(EmberBaseRecord):
    """
    payload schema for /power-sector-emissions endpoints.
    """
    series: str
    is_aggregate_series: bool
    emissions_mtco2: Optional[float] = None
    share_of_emissions_pct: Optional[float] = None

class EmberInstalledCapacityRecord(EmberBaseRecord):
    """
    payload schema for /installed-capacity endpoint.
    """
    series: str
    is_aggregate_series: bool
    capacity_gw: Optional[float] = None
    capacity_w_per_capita: Optional[float] = None

# --- GENERIC RESPONSE WRAPPER ---
# Create a Type Variable that must be a subclass of EmberBaseRecord
T = TypeVar('T', bound=EmberBaseRecord)

class EmberResponse(BaseModel, Generic[T]):
    """
    Validates the entire API payload structure.
    The 'data' list will strictly validate against whichever specific record type (T) is passed to it.
    """
    stats: Dict[str, Any]
    data: List[T]

class EmberAPIClient:
    '''
    stateless client for the Ember Energy API.
    '''
    def __init__(self, api_key: str, base_url: str="https://api.ember-energy.org/v1"):
        if not api_key:
            logger.error("Initialization failed: EMBER_API_KEY is missing")
            raise ValueError("EMBER_API_KEY is missing")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        retries = Retry(total=4, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        self.session.mount("https://", HTTPAdapter(max_retries=retries))
        self._is_closed = False # to manage session context
        logger.info("Initialized Ember Client", extra={"base_url": self.base_url})

    # ---- Context Management ----
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensures the requests session is closed."""
        self.session.close()
        self._is_closed = True
        logger.info("Client session closed.")
   
    def _get(self, endpoint: str, params: dict = None) -> dict:
        if self._is_closed:
            raise RuntimeError("Ember Client session is not active")
        url = f"{self.base_url}/{endpoint}" # construct url
        payload = dict(params or {})
        payload["api_key"] = self.api_key
        safe_params = {k: v for k, v in payload.items() if k != "api_key"}

        logger.info("Executing API request", extra={"endpoint": endpoint, "params": safe_params})
        response = self.session.get(url, params=payload, timeout=30)
        if response.status_code != 200:
            logger.error("Request Failed: ", extra={"status_code": response.status_code, "text": response.text[:100]})
            response.raise_for_status()
        return response.json()

    def get_yearly_generation(self, **kwargs) -> EmberResponse[EmberGenerationRecord]:
        """
        Fetches Yearly Electricity Generation data.
        """
        raw_json = self._get("electricity-generation/yearly", params=kwargs)
        return EmberResponse[EmberGenerationRecord](**raw_json)

    def get_monthly_generation(self, **kwargs) -> EmberResponse[EmberGenerationRecord]:
        """
        Fetches Monthly Electricity Generation data.
        """
        raw_json = self._get("electricity-generation/monthly", params=kwargs)
        return EmberResponse[EmberGenerationRecord](**raw_json)

    def get_yearly_demand(self, **kwargs) -> EmberResponse[EmberYearlyDemandRecord]:
        """Fetches Yearly Electricity Demand data."""
        raw_json = self._get("electricity-demand/yearly", params=kwargs)
        return EmberResponse[EmberYearlyDemandRecord](**raw_json)

    def get_monthly_demand(self, **kwargs) -> EmberResponse[EmberMonthlyDemandRecord]:
        """Fetches Monthly Electricity Demand data."""
        raw_json = self._get("electricity-demand/monthly", params=kwargs)
        return EmberResponse[EmberMonthlyDemandRecord](**raw_json)

    def get_yearly_carbon_intensity(self, **kwargs) -> EmberResponse[EmberCarbonIntensityRecord]:
        """Fetches Yearly Carbon Intensity data."""
        raw_json = self._get("carbon-intensity/yearly", params=kwargs)
        return EmberResponse[EmberCarbonIntensityRecord](**raw_json)

    def get_monthly_carbon_intensity(self, **kwargs) -> EmberResponse[EmberCarbonIntensityRecord]:
        """Fetches Monthly Carbon Intensity data."""
        raw_json = self._get("carbon-intensity/monthly", params=kwargs)
        return EmberResponse[EmberCarbonIntensityRecord](**raw_json)

    def get_yearly_power_sector_emission(self, **kwargs) -> EmberResponse[EmberPowerSectorEmissionRecord]:
        """
        Fetches Yearly Power Sector Emission data.
        """
        raw_json = self._get("power-sector-emissions/yearly", params=kwargs)
        return EmberResponse[EmberPowerSectorEmissionRecord](**raw_json)

    def get_monthly_power_sector_emission(self, **kwargs) -> EmberResponse[EmberPowerSectorEmissionRecord]:
        """
        Fetches Monthly Power Sector Emissionnoi, data.
        """
        raw_json = self._get("power-sector-emissions/monthly", params=kwargs)
        return EmberResponse[EmberPowerSectorEmissionRecord](**raw_json)

    def get_monthly_installed_capacity(self, **kwargs) -> EmberResponse[EmberInstalledCapacityRecord]:
        """
        Fetches Monthly Installed Capacity data.
        """
        raw_json = self._get("installed-capacity/monthly", params=kwargs)
        return EmberResponse[EmberInstalledCapacityRecord](**raw_json)

if __name__ == "__main__": # pragma: no cover
    import os
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("EMBER_API_KEY")

    with EmberAPIClient(api_key=api_key) as client:
        try:
            ## sample request params
            target_countries = "BRA,DEU,ZAF"
            energy_type = "Bioenergy,Wind"

            ## sample request for yearly electricity generation data
            yearly_generation_payload = client.get_yearly_generation(
                entity_code=target_countries,
                start_date="2020",
                end_date="2022",
                is_aggregate_entity = False,
                series = energy_type,
                is_aggregate_series=False,
            )

            if yearly_generation_payload.data:
                # print(generation_payload.data)
                first_rec = yearly_generation_payload.data[1]
                print(f"Sample: {first_rec.entity} generated {first_rec.generation_twh} TWh of {first_rec.series} in {first_rec.date}")

            # sample request for monthly electricity generation data
            monthly_generation_payload = client.get_monthly_generation(
                entity_code=target_countries,
                start_date="2020-01",
                end_date="2022-12",
                is_aggregate_entity = False,
                series = energy_type,
                is_aggregate_series=False,
            )

            if monthly_generation_payload.data:
                first_rec = monthly_generation_payload.data[1]
                print(f"Sample: {first_rec.entity} generated {first_rec.generation_twh} TWh of {first_rec.series} in {first_rec.date}")
           
            ## sample request for yearly carbon intensity data
            intensity_payload = client.get_yearly_carbon_intensity(
                entity_code=target_countries,
                start_date="2020",
                end_date="2022"
            )

            if intensity_payload.data:
                print(f"Intensity Records Fetched: {len(intensity_payload.data)}")
        except Exception as e:
            logger.error("Pipeline execution failed", exc_info=True)