import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DUCKDB_PATH = Path(os.getenv("DUCKDB_PATH", "data/charity_ledger.duckdb"))
RAW_DATA_PATH = Path(os.getenv("RAW_DATA_PATH", "data/raw"))
COMPANIES_HOUSE_API_KEY = os.getenv("COMPANIES_HOUSE_API_KEY", "")

CHARITY_COMMISSION_BULK_URL = (
    "https://ccewuksprdoneregsadata1.blob.core.windows.net/data/txt/publicextract.charity.zip"
)
CHARITY_COMMISSION_FINANCES_URL = (
    "https://ccewuksprdoneregsadata1.blob.core.windows.net/data/txt/publicextract.charity_annual_return_parta.zip"
)
CHARITY_COMMISSION_TRUSTEES_URL = (
    "https://ccewuksprdoneregsadata1.blob.core.windows.net/data/txt/publicextract.charity_trustee.zip"
)

GRANTNAV_BULK_URL = "https://grantnav.threesixtygiving.org/developers/data.json"

COMPANIES_HOUSE_BASE_URL = "https://api.company-information.service.gov.uk"
