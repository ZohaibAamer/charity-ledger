"""Companies House extractor.

Two paths into the warehouse:

* **Bulk**: the monthly "basic company data" snapshot, republished on
  the 1st of each month, loaded in full into ``bronze.ch_companies``.
* **API**: per-company enrichment (profile + filing history) for the
  companies that entity resolution has already linked to charities.
  Requires a free API key; skipped gracefully without one.
"""

import io
import zipfile
from datetime import UTC, datetime, timedelta

import duckdb
import httpx
import polars as pl

from extract.config import (
    COMPANIES_HOUSE_API_KEY,
    COMPANIES_HOUSE_BASE_URL,
    RAW_DATA_PATH,
)
from extract.loader import (
    add_extract_metadata,
    get_connection,
    load_to_bronze,
    utc_now_iso,
    write_watermark,
)
from extract.logging_setup import get_logger

log = get_logger(__name__)

SOURCE_NAME = "companies_house"

BULK_URL_TEMPLATE = (
    "https://download.companieshouse.gov.uk/BasicCompanyDataAsOneFile-{snapshot}.zip"
)

# How many charity-linked companies to enrich per run; keeps the free
# API tier's rate limit (600 req / 5 min) comfortable.
ENRICHMENT_BATCH_SIZE = 500


def _current_bulk_url() -> str:
    """Resolve this month's bulk snapshot URL, falling back one month.

    Companies House republishes the file on the 1st, but the exact
    publication time varies, so early in the month only the previous
    snapshot may exist.
    """
    today = datetime.now(UTC).date()
    current = today.replace(day=1)
    previous = (current - timedelta(days=1)).replace(day=1)

    for snapshot in (current, previous):
        url = BULK_URL_TEMPLATE.format(snapshot=snapshot.isoformat())
        resp = httpx.head(url, follow_redirects=True, timeout=30)
        if resp.status_code == 200:
            return url
    raise RuntimeError("No Companies House bulk snapshot found for current or previous month")


def extract_bulk() -> int:
    """Download the monthly snapshot and load it into bronze."""
    url = _current_bulk_url()
    log.info("Downloading Companies House bulk data from %s", url)
    resp = httpx.get(url, follow_redirects=True, timeout=600)
    resp.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        csv_names = [n for n in zf.namelist() if n.endswith(".csv")]
        with zf.open(csv_names[0]) as f:
            df = pl.read_csv(
                f.read(),
                infer_schema_length=10000,
                ignore_errors=True,
                truncate_ragged_lines=True,
            )

    cache_dir = RAW_DATA_PATH / SOURCE_NAME
    cache_dir.mkdir(parents=True, exist_ok=True)
    df.write_parquet(cache_dir / "basic_company_data.parquet")

    df = add_extract_metadata(df, SOURCE_NAME)
    count = load_to_bronze(df, "ch_companies")
    log.info("Loaded %s companies into bronze.ch_companies", f"{count:,}")
    return count


def fetch_company_profile(company_number: str) -> dict | None:
    """Fetch one company profile from the REST API; None on any miss."""
    if not COMPANIES_HOUSE_API_KEY:
        return None
    resp = httpx.get(
        f"{COMPANIES_HOUSE_BASE_URL}/company/{company_number}",
        auth=(COMPANIES_HOUSE_API_KEY, ""),
        timeout=30,
    )
    return resp.json() if resp.status_code == 200 else None


def fetch_filing_history(company_number: str, items_per_page: int = 25) -> list[dict]:
    """Fetch the most recent filings for a company; empty list on any miss."""
    if not COMPANIES_HOUSE_API_KEY:
        return []
    resp = httpx.get(
        f"{COMPANIES_HOUSE_BASE_URL}/company/{company_number}/filing-history",
        auth=(COMPANIES_HOUSE_API_KEY, ""),
        params={"items_per_page": items_per_page},
        timeout=30,
    )
    return resp.json().get("items", []) if resp.status_code == 200 else []


def enrich_charity_companies(company_numbers: list[str]) -> int:
    """Pull API profiles and filing history for charity-linked companies.

    Returns the number of profiles loaded. Both result sets replace
    their bronze tables wholesale: the API is the source of truth and
    the linked-company population is small.
    """
    if not COMPANIES_HOUSE_API_KEY:
        log.warning("Skipping API enrichment: COMPANIES_HOUSE_API_KEY not set")
        return 0

    profiles: list[dict] = []
    filings: list[dict] = []

    for i, company_number in enumerate(company_numbers):
        if profile := fetch_company_profile(company_number):
            profiles.append(profile)

        for filing in fetch_filing_history(company_number):
            filing["company_number"] = company_number
            filings.append(filing)

        if (i + 1) % 50 == 0:
            log.info("Enriched %d/%d companies", i + 1, len(company_numbers))

    if profiles:
        df_profiles = add_extract_metadata(pl.DataFrame(profiles), SOURCE_NAME)
        load_to_bronze(df_profiles, "ch_profiles", mode="replace")
        log.info("Loaded %d company profiles into bronze.ch_profiles", len(profiles))

    if filings:
        df_filings = add_extract_metadata(pl.DataFrame(filings), SOURCE_NAME)
        load_to_bronze(df_filings, "ch_filings", mode="replace")
        log.info("Loaded %d filing records into bronze.ch_filings", len(filings))

    return len(profiles)


def _resolved_company_numbers(limit: int = ENRICHMENT_BATCH_SIZE) -> list[str]:
    """Company numbers already linked to charities by entity resolution.

    Returns an empty list on the first run, before dbt has built the
    silver layer.
    """
    con = get_connection()
    try:
        rows = con.execute(
            "SELECT DISTINCT company_number FROM silver.entity_resolution "
            "WHERE company_number IS NOT NULL LIMIT ?",
            [limit],
        ).fetchall()
        return [r[0] for r in rows]
    except duckdb.CatalogException:
        log.info("Entity resolution table not found yet; skipping API enrichment")
        return []
    finally:
        con.close()


def run() -> None:
    """Extract the bulk snapshot, then enrich charity-linked companies."""
    extract_bulk()

    if company_numbers := _resolved_company_numbers():
        enrich_charity_companies(company_numbers)

    write_watermark(SOURCE_NAME, utc_now_iso())
    log.info("Companies House extract complete")


if __name__ == "__main__":
    run()
