"""360Giving GrantNav extractor.

GrantNav publishes a JSON index of every participating funder's grant
dataset. Each dataset is fetched individually (CSV or JSON), flattened
to a tabular shape, and concatenated into ``bronze.gn_grants``.
"""

from pathlib import Path

import httpx
import polars as pl

from extract.config import GRANTNAV_BULK_URL, RAW_DATA_PATH
from extract.loader import add_extract_metadata, load_to_bronze, utc_now_iso, write_watermark
from extract.logging_setup import get_logger

log = get_logger(__name__)

SOURCE_NAME = "grantnav"


def _flatten_columns(df: pl.DataFrame) -> pl.DataFrame:
    """Flatten nested 360Giving JSON into underscore-separated columns.

    The 360Giving schema nests organisations and programmes as lists of
    structs (e.g. ``recipientOrganization[0].name``). The bronze layer
    needs flat columns, so lists are reduced to their first element and
    structs are unnested as ``parent_child``.
    """
    flat_cols = []
    for col in df.columns:
        if df[col].dtype == pl.Struct:
            unnested = df.select(pl.col(col).struct.unnest())
            flat_cols.extend(
                unnested[sub_col].alias(f"{col}_{sub_col}") for sub_col in unnested.columns
            )
        elif df[col].dtype == pl.List:
            flat_cols.append(df[col].list.get(0).alias(col))
        else:
            flat_cols.append(df[col])
    return pl.DataFrame(flat_cols)


def _fetch_data_index() -> list[dict]:
    """Fetch the GrantNav registry of publisher dataset URLs."""
    log.info("Fetching GrantNav data index")
    resp = httpx.get(GRANTNAV_BULK_URL, follow_redirects=True, timeout=60)
    resp.raise_for_status()
    return resp.json()


def _download_grants_csv(url: str) -> pl.DataFrame | None:
    """Download one publisher's CSV dataset; None if it cannot be parsed."""
    try:
        resp = httpx.get(url, follow_redirects=True, timeout=120)
        resp.raise_for_status()
        return pl.read_csv(
            resp.content,
            infer_schema_length=5000,
            ignore_errors=True,
            truncate_ragged_lines=True,
        )
    except Exception as exc:  # one bad publisher must not sink the run
        log.warning("Skipping %s: %s", url, exc)
        return None


def _download_grants_json(url: str) -> pl.DataFrame | None:
    """Download one publisher's 360Giving JSON dataset; None on failure."""
    try:
        resp = httpx.get(url, follow_redirects=True, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        grants = data.get("grants", data) if isinstance(data, dict) else data
        if isinstance(grants, list) and grants:
            return _flatten_columns(pl.from_dicts(grants))
        return None
    except Exception as exc:  # one bad publisher must not sink the run
        log.warning("Skipping %s: %s", url, exc)
        return None


def extract_grants(max_publishers: int | None = None) -> int:
    """Download every publisher dataset and load the union into bronze.

    Args:
        max_publishers: Optional cap for smoke tests and local runs.
    """
    index = _fetch_data_index()
    publishers = index if max_publishers is None else index[:max_publishers]

    frames: list[pl.DataFrame] = []
    for i, entry in enumerate(publishers):
        download_url = entry.get("distribution", [{}])[0].get("downloadURL", "")
        if not download_url:
            continue

        log.info("[%d/%d] %s", i + 1, len(publishers), entry.get("title", "unknown"))

        if download_url.endswith(".csv"):
            df = _download_grants_csv(download_url)
        else:
            df = _download_grants_json(download_url)

        if df is not None and len(df) > 0:
            frames.append(df)

    if not frames:
        log.warning("No grant data downloaded")
        return 0

    combined = pl.concat(frames, how="diagonal_relaxed")

    cache_dir: Path = RAW_DATA_PATH / SOURCE_NAME
    cache_dir.mkdir(parents=True, exist_ok=True)
    combined.write_parquet(cache_dir / "grants.parquet")

    combined = add_extract_metadata(combined, SOURCE_NAME)
    count = load_to_bronze(combined, "gn_grants")
    log.info("Loaded %s grants from %d publishers", f"{count:,}", len(frames))
    return count


def run() -> None:
    """Extract all GrantNav publisher datasets."""
    extract_grants()
    write_watermark(SOURCE_NAME, utc_now_iso())
    log.info("GrantNav extract complete")


if __name__ == "__main__":
    run()
