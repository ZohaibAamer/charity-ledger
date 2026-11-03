"""Charity Commission register extractor.

The Commission publishes daily bulk ZIP extracts of the full register.
Three datasets feed the warehouse: charity details, annual return
finances, and trustees. Each lands in its own bronze table.
"""

import io
import zipfile
from pathlib import Path

import httpx
import polars as pl

from extract.config import (
    CHARITY_COMMISSION_BULK_URL,
    CHARITY_COMMISSION_FINANCES_URL,
    CHARITY_COMMISSION_TRUSTEES_URL,
    RAW_DATA_PATH,
)
from extract.loader import add_extract_metadata, load_to_bronze, utc_now_iso, write_watermark
from extract.logging_setup import get_logger

log = get_logger(__name__)

SOURCE_NAME = "charity_commission"

# (bulk URL, bronze table name) for each published dataset
DATASETS = [
    (CHARITY_COMMISSION_BULK_URL, "cc_charities"),
    (CHARITY_COMMISSION_FINANCES_URL, "cc_finances"),
    (CHARITY_COMMISSION_TRUSTEES_URL, "cc_trustees"),
]


def _download_and_extract_csv(url: str, cache_dir: Path | None = None) -> pl.DataFrame:
    """Download a ZIP containing one CSV and return it as a DataFrame.

    When ``cache_dir`` is given, the parsed frame is also cached locally
    as Parquet so a failed downstream step can be replayed without
    re-downloading.
    """
    log.info("Downloading %s", url)
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
        cache_path = (cache_dir / csv_names[0]).with_suffix(".parquet")
        df.write_parquet(cache_path)
        log.debug("Cached raw extract to %s", cache_path)

    return df


def extract_dataset(url: str, table_name: str) -> int:
    """Download one bulk dataset and load it into its bronze table."""
    df = _download_and_extract_csv(url, RAW_DATA_PATH / SOURCE_NAME)
    df = add_extract_metadata(df, SOURCE_NAME)
    count = load_to_bronze(df, table_name)
    log.info("Loaded %s rows into bronze.%s", f"{count:,}", table_name)
    return count


def run() -> None:
    """Extract all three Charity Commission datasets."""
    for url, table_name in DATASETS:
        extract_dataset(url, table_name)
    write_watermark(SOURCE_NAME, utc_now_iso())
    log.info("Charity Commission extract complete")


if __name__ == "__main__":
    run()
