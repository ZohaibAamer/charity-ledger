"""Pipeline configuration, resolved once at import time.

All deployment-specific values come from the environment (optionally
via a local ``.env`` file); source URLs that are stable public
endpoints live here as constants.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --- Warehouse paths -------------------------------------------------------
DUCKDB_PATH = Path(os.getenv("DUCKDB_PATH", "data/charity_ledger.duckdb"))
RAW_DATA_PATH = Path(os.getenv("RAW_DATA_PATH", "data/raw"))

# --- Source APIs -----------------------------------------------------------
COMPANIES_HOUSE_API_KEY = os.getenv("COMPANIES_HOUSE_API_KEY", "")
COMPANIES_HOUSE_BASE_URL = "https://api.company-information.service.gov.uk"

CHARITY_COMMISSION_BULK_URL = (
    "https://ccewuksprdoneregsadata1.blob.core.windows.net/data/txt/publicextract.charity.zip"
)
CHARITY_COMMISSION_FINANCES_URL = (
    "https://ccewuksprdoneregsadata1.blob.core.windows.net"
    "/data/txt/publicextract.charity_annual_return_parta.zip"
)
CHARITY_COMMISSION_TRUSTEES_URL = (
    "https://ccewuksprdoneregsadata1.blob.core.windows.net"
    "/data/txt/publicextract.charity_trustee.zip"
)

GRANTNAV_BULK_URL = "https://grantnav.threesixtygiving.org/developers/data.json"

# --- Azure Data Lake Storage Gen2 ------------------------------------------
ADLS_STORAGE_ACCOUNT = os.getenv("ADLS_STORAGE_ACCOUNT", "")
ADLS_CONTAINER = os.getenv("ADLS_CONTAINER", "charity-data")
ADLS_CREDENTIAL = os.getenv("ADLS_CREDENTIAL", "")

# --- Amazon S3 -------------------------------------------------------------
S3_BUCKET = os.getenv("S3_BUCKET", "")
S3_REGION = os.getenv("S3_REGION", "eu-west-2")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")

# --- Snowflake -------------------------------------------------------------
SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT", "")
SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER", "")
SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD", "")
SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE", "CHARITY_DATA")
SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_SCHEMA", "RAW")
SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")
SNOWFLAKE_ROLE = os.getenv("SNOWFLAKE_ROLE", "")
