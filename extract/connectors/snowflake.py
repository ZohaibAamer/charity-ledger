"""Snowflake connector.

Reads tables and query results from Snowflake into Polars
DataFrames for loading into the local DuckDB warehouse.
"""
from datetime import datetime

import polars as pl

from extract.loader import load_to_bronze, write_watermark


def _get_connection_uri(
    account: str,
    user: str,
    password: str,
    database: str,
    schema: str = "PUBLIC",
    warehouse: str = "COMPUTE_WH",
    role: str | None = None,
) -> str:
    uri = (
        f"snowflake://{user}:{password}@{account}"
        f"/{database}/{schema}?warehouse={warehouse}"
    )
    if role:
        uri += f"&role={role}"
    return uri


def read_table_from_snowflake(
    account: str,
    user: str,
    password: str,
    database: str,
    schema: str,
    table: str,
    warehouse: str = "COMPUTE_WH",
    role: str | None = None,
) -> pl.DataFrame:
    """Read a full table from Snowflake."""
    uri = _get_connection_uri(account, user, password, database, schema, warehouse, role)
    query = f'SELECT * FROM "{database}"."{schema}"."{table}"'
    return pl.read_database_uri(query, uri)


def read_query_from_snowflake(
    account: str,
    user: str,
    password: str,
    database: str,
    query: str,
    schema: str = "PUBLIC",
    warehouse: str = "COMPUTE_WH",
    role: str | None = None,
) -> pl.DataFrame:
    """Execute a query against Snowflake and return results."""
    uri = _get_connection_uri(account, user, password, database, schema, warehouse, role)
    return pl.read_database_uri(query, uri)


def read_incremental_from_snowflake(
    account: str,
    user: str,
    password: str,
    database: str,
    schema: str,
    table: str,
    watermark_column: str,
    last_watermark: str | None = None,
    warehouse: str = "COMPUTE_WH",
    role: str | None = None,
) -> pl.DataFrame:
    """Read rows from Snowflake newer than the last watermark."""
    uri = _get_connection_uri(account, user, password, database, schema, warehouse, role)

    if last_watermark:
        query = (
            f'SELECT * FROM "{database}"."{schema}"."{table}" '
            f"WHERE \"{watermark_column}\" > '{last_watermark}'"
        )
    else:
        query = f'SELECT * FROM "{database}"."{schema}"."{table}"'

    return pl.read_database_uri(query, uri)


def ingest_from_snowflake(
    account: str,
    user: str,
    password: str,
    database: str,
    schema: str,
    table: str,
    target_table: str,
    warehouse: str = "COMPUTE_WH",
    role: str | None = None,
    watermark_column: str | None = None,
    mode: str = "replace",
) -> int:
    """Ingest a Snowflake table into a bronze table."""
    source_ref = f"{account}/{database}.{schema}.{table}"
    print(f"Reading from snowflake://{source_ref}...")

    last_watermark = None
    if watermark_column:
        from extract.loader import read_watermark
        last_watermark = read_watermark(f"sf_{target_table}")

    if watermark_column and last_watermark:
        df = read_incremental_from_snowflake(
            account, user, password, database, schema, table,
            watermark_column, last_watermark, warehouse, role,
        )
        mode = "append"
    else:
        df = read_table_from_snowflake(
            account, user, password, database, schema, table,
            warehouse, role,
        )

    df = df.with_columns(
        pl.lit(datetime.utcnow().isoformat()).alias("_extracted_at"),
        pl.lit(f"snowflake://{source_ref}").alias("_source"),
    )

    count = load_to_bronze(df, target_table, mode=mode)

    new_watermark = datetime.utcnow().isoformat()
    if watermark_column:
        max_val = df.select(pl.col(watermark_column).max()).item()
        if max_val is not None:
            new_watermark = str(max_val)
    write_watermark(f"sf_{target_table}", new_watermark)

    print(f"Loaded {count:,} rows from Snowflake into {target_table}")
    return count
