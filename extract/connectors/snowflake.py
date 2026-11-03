"""Snowflake connector.

Reads tables or query results from Snowflake into the bronze layer.
Supports watermark-based incremental reads: when a watermark column
is configured, only rows newer than the last recorded high-water mark
are pulled and appended.
"""

import polars as pl

from extract.loader import (
    add_extract_metadata,
    load_to_bronze,
    read_watermark,
    utc_now_iso,
    write_watermark,
)
from extract.logging_setup import get_logger

log = get_logger(__name__)


def _connection_uri(
    account: str,
    user: str,
    password: str,
    database: str,
    schema: str = "PUBLIC",
    warehouse: str = "COMPUTE_WH",
    role: str | None = None,
) -> str:
    """Build the connectorx URI for a Snowflake session."""
    uri = f"snowflake://{user}:{password}@{account}/{database}/{schema}?warehouse={warehouse}"
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
    uri = _connection_uri(account, user, password, database, schema, warehouse, role)
    query = f'select * from "{database}"."{schema}"."{table}"'
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
    """Execute an arbitrary query against Snowflake and return the result."""
    uri = _connection_uri(account, user, password, database, schema, warehouse, role)
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
    """Read only the rows newer than the last recorded watermark."""
    uri = _connection_uri(account, user, password, database, schema, warehouse, role)
    query = f'select * from "{database}"."{schema}"."{table}"'
    if last_watermark:
        query += f" where \"{watermark_column}\" > '{last_watermark}'"
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
    """Ingest a Snowflake table into ``bronze.<target_table>``.

    With a ``watermark_column`` and an existing watermark, reads
    incrementally and appends; otherwise reads the full table using
    the given ``mode``. The new watermark is the max value seen in the
    watermark column, falling back to the wall-clock time.

    Returns the number of rows in the target table after the load.
    """
    source_ref = f"{account}/{database}.{schema}.{table}"
    log.info("Reading snowflake://%s", source_ref)

    last_watermark = read_watermark(f"sf_{target_table}") if watermark_column else None

    if watermark_column and last_watermark:
        df = read_incremental_from_snowflake(
            account,
            user,
            password,
            database,
            schema,
            table,
            watermark_column,
            last_watermark,
            warehouse,
            role,
        )
        mode = "append"
    else:
        df = read_table_from_snowflake(
            account, user, password, database, schema, table, warehouse, role
        )

    df = add_extract_metadata(df, f"snowflake://{source_ref}")
    count = load_to_bronze(df, target_table, mode=mode)

    new_watermark = utc_now_iso()
    if watermark_column:
        max_val = df.select(pl.col(watermark_column).max()).item()
        if max_val is not None:
            new_watermark = str(max_val)
    write_watermark(f"sf_{target_table}", new_watermark)

    log.info("Loaded %s rows from Snowflake into bronze.%s", f"{count:,}", target_table)
    return count
