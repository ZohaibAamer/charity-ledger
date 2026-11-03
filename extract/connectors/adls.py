"""Azure Data Lake Storage Gen2 connector.

Reads Parquet and Delta tables from ADLS containers using
Azure identity credentials or connection strings.
"""
from datetime import datetime

import polars as pl

from extract.loader import load_to_bronze, write_watermark


def read_parquet_from_adls(
    storage_account: str,
    container: str,
    path: str,
    credential: str | None = None,
) -> pl.DataFrame:
    """Read a Parquet file or directory from ADLS Gen2."""
    if credential:
        storage_options = {"account_name": storage_account, "account_key": credential}
    else:
        storage_options = {"account_name": storage_account, "use_azure_cli": "true"}

    uri = f"az://{container}/{path}"
    return pl.read_parquet(uri, storage_options=storage_options)


def read_delta_from_adls(
    storage_account: str,
    container: str,
    path: str,
    credential: str | None = None,
) -> pl.DataFrame:
    """Read a Delta Lake table from ADLS Gen2."""
    if credential:
        storage_options = {"account_name": storage_account, "account_key": credential}
    else:
        storage_options = {"account_name": storage_account, "use_azure_cli": "true"}

    uri = f"az://{container}/{path}"
    return pl.read_delta(uri, storage_options=storage_options)


def ingest_from_adls(
    storage_account: str,
    container: str,
    path: str,
    table_name: str,
    credential: str | None = None,
    file_format: str = "parquet",
) -> int:
    """Ingest data from ADLS into a bronze table."""
    print(f"Reading from adls://{storage_account}/{container}/{path}...")

    if file_format == "delta":
        df = read_delta_from_adls(storage_account, container, path, credential)
    else:
        df = read_parquet_from_adls(storage_account, container, path, credential)

    df = df.with_columns(
        pl.lit(datetime.utcnow().isoformat()).alias("_extracted_at"),
        pl.lit(f"adls://{storage_account}/{container}").alias("_source"),
    )

    count = load_to_bronze(df, table_name)
    write_watermark(f"adls_{table_name}", datetime.utcnow().isoformat())
    print(f"Loaded {count:,} rows from ADLS into {table_name}")
    return count
