"""Extract Companies House data via bulk download and REST API.

Bulk: monthly snapshot of basic company data.
API: enrichment for companies linked to charities (accounts filing dates, SIC codes).
"""
import io
import zipfile
from datetime import datetime, timedelta

import duckdb
import httpx
import polars as pl

from extract.config import (
    COMPANIES_HOUSE_API_KEY,
    COMPANIES_HOUSE_BASE_URL,
    RAW_DATA_PATH,
)
from extract.loader import load_to_bronze, write_watermark

SOURCE_NAME = "companies_house"

BULK_URL_TEMPLATE = (
    "https://download.companieshouse.gov.uk/BasicCompanyDataAsOneFile-{snapshot}.zip"
)


def _current_bulk_url() -> str:
    """Companies House publishes a new snapshot on the 1st of each month.

    Try the current month first; fall back to the previous month if the
    current snapshot is not yet published.
    """
    today = datetime.utcnow().date()
    current = today.replace(day=1)
    prev = (current - timedelta(days=1)).replace(day=1)

    for snapshot in (current, prev):
        url = BULK_URL_TEMPLATE.format(snapshot=snapshot.isoformat())
        resp = httpx.head(url, follow_redirects=True, timeout=30)
        if resp.status_code == 200:
            return url
    raise RuntimeError("No Companies House bulk snapshot found for current or previous month")


def _add_extract_metadata(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(
        pl.lit(datetime.utcnow().isoformat()).alias("_extracted_at"),
        pl.lit(SOURCE_NAME).alias("_source"),
    )


def extract_bulk() -> int:
    url = _current_bulk_url()
    print(f"Downloading Companies House bulk data from {url}...")
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

    df = _add_extract_metadata(df)
    count = load_to_bronze(df, "ch_companies")
    print(f"Loaded {count:,} companies")
    return count


def fetch_company_profile(company_number: str) -> dict | None:
    if not COMPANIES_HOUSE_API_KEY:
        return None
    resp = httpx.get(
        f"{COMPANIES_HOUSE_BASE_URL}/company/{company_number}",
        auth=(COMPANIES_HOUSE_API_KEY, ""),
        timeout=30,
    )
    if resp.status_code == 200:
        return resp.json()
    return None


def fetch_filing_history(company_number: str, items_per_page: int = 25) -> list[dict]:
    if not COMPANIES_HOUSE_API_KEY:
        return []
    resp = httpx.get(
        f"{COMPANIES_HOUSE_BASE_URL}/company/{company_number}/filing-history",
        auth=(COMPANIES_HOUSE_API_KEY, ""),
        params={"items_per_page": items_per_page},
        timeout=30,
    )
    if resp.status_code == 200:
        return resp.json().get("items", [])
    return []


def enrich_charity_companies(company_numbers: list[str]) -> int:
    if not COMPANIES_HOUSE_API_KEY:
        print("Skipping API enrichment: COMPANIES_HOUSE_API_KEY not set")
        return 0

    profiles = []
    filings = []

    for i, cn in enumerate(company_numbers):
        profile = fetch_company_profile(cn)
        if profile:
            profiles.append(profile)

        history = fetch_filing_history(cn)
        for filing in history:
            filing["company_number"] = cn
            filings.append(filing)

        if (i + 1) % 50 == 0:
            print(f"  Enriched {i + 1}/{len(company_numbers)} companies")

    if profiles:
        df_profiles = _add_extract_metadata(pl.DataFrame(profiles))
        load_to_bronze(df_profiles, "ch_profiles", mode="replace")
        print(f"Loaded {len(profiles)} company profiles")

    if filings:
        df_filings = _add_extract_metadata(pl.DataFrame(filings))
        load_to_bronze(df_filings, "ch_filings", mode="replace")
        print(f"Loaded {len(filings)} filing records")

    return len(profiles)


def _resolved_company_numbers(limit: int = 500) -> list[str]:
    """Company numbers already linked to charities by entity resolution.

    Returns an empty list on the first run, before the silver layer exists.
    """
    from extract.loader import get_connection

    con = get_connection()
    try:
        rows = con.execute(
            "SELECT DISTINCT company_number FROM silver.entity_resolution "
            "WHERE company_number IS NOT NULL LIMIT ?",
            [limit],
        ).fetchall()
        return [r[0] for r in rows]
    except duckdb.CatalogException:
        print("Entity resolution table not found yet; skipping API enrichment")
        return []
    finally:
        con.close()


def run():
    extract_bulk()

    company_numbers = _resolved_company_numbers()
    if company_numbers:
        enrich_charity_companies(company_numbers)

    write_watermark(SOURCE_NAME, datetime.utcnow().isoformat())
    print("Companies House extract complete.")


if __name__ == "__main__":
    run()
