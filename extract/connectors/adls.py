"""Azure Data Lake Storage Gen2 connector.

Reads Parquet files or Delta tables from an ADLS container into the
bronze layer. Authenticates with an account key when one is supplied,
otherwise falls back to the ambient Azure CLI login.
"""

import polars as pl

from extract.loader import add_extract_metadata, load_to_bronze, utc_now_iso, write_watermark
from extract.logging_setup import get_logger

log = get_logger(__name__)


def _storage_options(storage_account: str, credential: str | None) -> dict[str, str]:
    """Build fsspec storage options for key-based or CLI-based auth."""
    if credential:
        return {"account_name": storage_account, "account_key": credential}
    return {"account_name": storage_account, "use_azure_cli": "true"}


def read_parquet_from_adls(
    storage_account: str,
    container: str,
    path: str,
    credential: str | None = None,
) -> pl.DataFrame:
    """Read a Parquet file or directory from ADLS Gen2."""
    uri = f"az://{container}/{path}"
    return pl.read_parquet(uri, storage_options=_storage_options(storage_account, credential))


def read_delta_from_adls(
    storage_account: str,
    container: str,
    path: str,
    credential: str | None = None,
) -> pl.DataFrame:
    """Read a Delta Lake table from ADLS Gen2."""
    uri = f"az://{container}/{path}"
    return pl.read_delta(uri, storage_options=_storage_options(storage_account, credential))


def ingest_from_adls(
    storage_account: str,
    container: str,
    path: str,
    table_name: str,
    credential: str | None = None,
    file_format: str = "parquet",
) -> int:
    """Ingest an ADLS dataset into ``bronze.<table_name>``.

    Args:
        file_format: ``parquet`` (default) or ``delta``.

    Returns the number of rows loaded.
    """
    log.info("Reading adls://%s/%s/%s", storage_account, container, path)

    reader = read_delta_from_adls if file_format == "delta" else read_parquet_from_adls
    df = reader(storage_account, container, path, credential)
    df = add_extract_metadata(df, f"adls://{storage_account}/{container}")

    count = load_to_bronze(df, table_name)
    write_watermark(f"adls_{table_name}", utc_now_iso())
    log.info("Loaded %s rows from ADLS into bronze.%s", f"{count:,}", table_name)
    return count
