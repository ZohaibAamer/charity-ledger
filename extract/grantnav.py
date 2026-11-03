"""Extract 360Giving GrantNav grant data.

Downloads the GrantNav bulk data index, then fetches individual
publisher datasets and loads them into bronze DuckDB tables.
"""
from datetime import datetime

import httpx
import polars as pl

from extract.config import GRANTNAV_BULK_URL, RAW_DATA_PATH
from extract.loader import load_to_bronze, write_watermark

SOURCE_NAME = "grantnav"


def _add_extract_metadata(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(
        pl.lit(datetime.utcnow().isoformat()).alias("_extracted_at"),
        pl.lit(SOURCE_NAME).alias("_source"),
    )


def _fetch_data_index() -> list[dict]:
    print("Fetching GrantNav data index...")
    resp = httpx.get(GRANTNAV_BULK_URL, follow_redirects=True, timeout=60)
    resp.raise_for_status()
    return resp.json()


def _download_grants_csv(url: str) -> pl.DataFrame | None:
    try:
        resp = httpx.get(url, follow_redirects=True, timeout=120)
        resp.raise_for_status()
        return pl.read_csv(
            resp.content,
            infer_schema_length=5000,
            ignore_errors=True,
            truncate_ragged_lines=True,
        )
    except Exception as e:
        print(f"  Skipping {url}: {e}")
        return None


def _download_grants_json(url: str) -> pl.DataFrame | None:
    try:
        resp = httpx.get(url, follow_redirects=True, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        grants = data.get("grants", data) if isinstance(data, dict) else data
        if isinstance(grants, list) and grants:
            return pl.DataFrame(grants)
        return None
    except Exception as e:
        print(f"  Skipping {url}: {e}")
        return None


def extract_grants(max_publishers: int | None = None) -> int:
    index = _fetch_data_index()

    all_grants = []
    publishers = index if max_publishers is None else index[:max_publishers]

    for i, entry in enumerate(publishers):
        download_url = entry.get("distribution", [{}])[0].get("downloadURL", "")
        title = entry.get("title", "unknown")

        if not download_url:
            continue

        print(f"  [{i + 1}/{len(publishers)}] {title}")

        if download_url.endswith(".csv"):
            df = _download_grants_csv(download_url)
        else:
            df = _download_grants_json(download_url)

        if df is not None and len(df) > 0:
            all_grants.append(df)

    if not all_grants:
        print("No grant data downloaded")
        return 0

    combined = pl.concat(all_grants, how="diagonal_relaxed")

    cache_dir = RAW_DATA_PATH / SOURCE_NAME
    cache_dir.mkdir(parents=True, exist_ok=True)
    combined.write_parquet(cache_dir / "grants.parquet")

    combined = _add_extract_metadata(combined)
    count = load_to_bronze(combined, "gn_grants")
    print(f"Loaded {count:,} grants from {len(all_grants)} publishers")
    return count


def run():
    extract_grants()
    write_watermark(SOURCE_NAME, datetime.utcnow().isoformat())
    print("GrantNav extract complete.")


if __name__ == "__main__":
    run()
