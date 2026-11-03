"""DuckDB warehouse access: bronze loading, metadata, and watermarks.

This module is the single write path into the warehouse. Extractors
hand it Polars DataFrames; it owns schema creation, lineage columns,
and the incremental-load watermark table (``meta.watermarks``).
"""

from datetime import UTC, datetime

import duckdb
import polars as pl

from extract.config import DUCKDB_PATH

BRONZE_SCHEMA = "bronze"
META_SCHEMA = "meta"

_WATERMARKS_DDL = (
    f"CREATE TABLE IF NOT EXISTS {META_SCHEMA}.watermarks ("
    "source_name VARCHAR PRIMARY KEY, "
    "watermark VARCHAR, "
    "updated_at TIMESTAMP DEFAULT current_timestamp)"
)


def utc_now_iso() -> str:
    """Current UTC time as an ISO-8601 string, used for lineage stamps."""
    return datetime.now(UTC).isoformat()


def get_connection() -> duckdb.DuckDBPyConnection:
    """Open a connection to the warehouse file, creating its folder if needed."""
    DUCKDB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(DUCKDB_PATH))


def add_extract_metadata(df: pl.DataFrame, source_name: str) -> pl.DataFrame:
    """Append the lineage columns every bronze table must carry.

    ``_extracted_at`` records when the extraction ran; ``_source``
    records which system the rows came from. Both are required by
    the bronze data contract.
    """
    return df.with_columns(
        pl.lit(utc_now_iso()).alias("_extracted_at"),
        pl.lit(source_name).alias("_source"),
    )


def load_to_bronze(df: pl.DataFrame, table_name: str, mode: str = "replace") -> int:
    """Load a DataFrame into ``bronze.<table_name>`` and return the row count.

    Args:
        df: The frame to load. Must already carry lineage columns.
        table_name: Target table name inside the bronze schema.
        mode: ``replace`` drops and recreates the table (full snapshot
            sources); ``append`` inserts, creating the table on first run
            (incremental sources).
    """
    con = get_connection()
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {BRONZE_SCHEMA}")
    con.register("df_view", df)

    full_table = f"{BRONZE_SCHEMA}.{table_name}"

    if mode == "replace":
        con.execute(f"DROP TABLE IF EXISTS {full_table}")
        con.execute(f"CREATE TABLE {full_table} AS SELECT * FROM df_view")
    elif mode == "append":
        try:
            con.execute(f"INSERT INTO {full_table} SELECT * FROM df_view")
        except duckdb.CatalogException:
            con.execute(f"CREATE TABLE {full_table} AS SELECT * FROM df_view")
    else:
        con.close()
        raise ValueError(f"Unknown load mode: {mode!r} (expected 'replace' or 'append')")

    count = con.execute(f"SELECT count(*) FROM {full_table}").fetchone()[0]
    con.close()
    return count


def read_watermark(source_name: str) -> str | None:
    """Return the last recorded watermark for a source, or None on first run."""
    con = get_connection()
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {META_SCHEMA}")
    con.execute(_WATERMARKS_DDL)
    row = con.execute(
        f"SELECT watermark FROM {META_SCHEMA}.watermarks WHERE source_name = ?",
        [source_name],
    ).fetchone()
    con.close()
    return row[0] if row else None


def write_watermark(source_name: str, watermark: str) -> None:
    """Record the high-water mark a source has been loaded up to."""
    con = get_connection()
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {META_SCHEMA}")
    con.execute(_WATERMARKS_DDL)
    con.execute(
        f"INSERT OR REPLACE INTO {META_SCHEMA}.watermarks "
        "(source_name, watermark, updated_at) VALUES (?, ?, current_timestamp)",
        [source_name, watermark],
    )
    con.close()
