"""Extract Charity Commission register data from bulk ZIP downloads.

Loads charity details, annual financial returns, and trustee data
into bronze tables in DuckDB.
"""
import io
import zipfile
from datetime import datetime

import httpx
import polars as pl

from extract.config import (
    CHARITY_COMMISSION_BULK_URL,
    CHARITY_COMMISSION_FINANCES_URL,
    CHARITY_COMMISSION_TRUSTEES_URL,
    RAW_DATA_PATH,
)
from extract.loader import load_to_bronze, write_watermark

SOURCE_NAME = "charity_commission"


def _download_and_extract_csv(url: str, cache_dir=None) -> pl.DataFrame:
    """Download a ZIP file containing a single CSV and return as DataFrame."""
    print(f"Downloading {url}...")
    resp = httpx.get(url, follow_redirects=True, timeout=300)
    resp.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        csv_names = [n for n in zf.namelist() if n.endswith(".csv")]
        if not csv_names:
            raise ValueError(f"No CSV found in {url}")
        with zf.open(csv_names[0]) as f:
            df = pl.read_csv(
                f.read(),
                infer_schema_length=10000,
                ignore_errors=True,
                truncate_ragged_lines=True,
            )

    if cache_dir:
        cache_dir.mkdir(parents=True, exist_ok=True)
        path = cache_dir / csv_names[0]
        df.write_parquet(path.with_suffix(".parquet"))
        print(f"  Cached to {path.with_suffix('.parquet')}")

    return df


def _add_extract_metadata(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(
        pl.lit(datetime.utcnow().isoformat()).alias("_extracted_at"),
        pl.lit(SOURCE_NAME).alias("_source"),
    )


def extract_charities() -> int:
    df = _download_and_extract_csv(
        CHARITY_COMMISSION_BULK_URL, RAW_DATA_PATH / SOURCE_NAME
    )
    df = _add_extract_metadata(df)
    count = load_to_bronze(df, "cc_charities")
    print(f"Loaded {count:,} charities")
    return count


def extract_finances() -> int:
    df = _download_and_extract_csv(
        CHARITY_COMMISSION_FINANCES_URL, RAW_DATA_PATH / SOURCE_NAME
    )
    df = _add_extract_metadata(df)
    count = load_to_bronze(df, "cc_finances")
    print(f"Loaded {count:,} financial records")
    return count


def extract_trustees() -> int:
    df = _download_and_extract_csv(
        CHARITY_COMMISSION_TRUSTEES_URL, RAW_DATA_PATH / SOURCE_NAME
    )
    df = _add_extract_metadata(df)
    count = load_to_bronze(df, "cc_trustees")
    print(f"Loaded {count:,} trustee records")
    return count


def run():
    extract_charities()
    extract_finances()
    extract_trustees()
    write_watermark(SOURCE_NAME, datetime.utcnow().isoformat())
    print("Charity Commission extract complete.")


if __name__ == "__main__":
    run()
