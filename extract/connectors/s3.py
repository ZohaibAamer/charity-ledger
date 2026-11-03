"""Amazon S3 connector.

Reads Parquet files or Delta tables from an S3 bucket into the bronze
layer. Uses explicit keys when supplied, otherwise the ambient AWS
credential chain (IAM role, profile, environment).
"""

import polars as pl

from extract.loader import add_extract_metadata, load_to_bronze, utc_now_iso, write_watermark
from extract.logging_setup import get_logger

log = get_logger(__name__)


def _storage_options(
    region: str,
    aws_access_key_id: str | None,
    aws_secret_access_key: str | None,
) -> dict[str, str]:
    """Build fsspec storage options for key-based or ambient-chain auth."""
    options = {"aws_region": region}
    if aws_access_key_id and aws_secret_access_key:
        options["aws_access_key_id"] = aws_access_key_id
        options["aws_secret_access_key"] = aws_secret_access_key
    return options


def read_parquet_from_s3(
    bucket: str,
    key: str,
    region: str = "eu-west-2",
    aws_access_key_id: str | None = None,
    aws_secret_access_key: str | None = None,
) -> pl.DataFrame:
    """Read a Parquet file or prefix from S3."""
    uri = f"s3://{bucket}/{key}"
    options = _storage_options(region, aws_access_key_id, aws_secret_access_key)
    return pl.read_parquet(uri, storage_options=options)


def read_delta_from_s3(
    bucket: str,
    key: str,
    region: str = "eu-west-2",
    aws_access_key_id: str | None = None,
    aws_secret_access_key: str | None = None,
) -> pl.DataFrame:
    """Read a Delta Lake table from S3."""
    uri = f"s3://{bucket}/{key}"
    options = _storage_options(region, aws_access_key_id, aws_secret_access_key)
    return pl.read_delta(uri, storage_options=options)


def ingest_from_s3(
    bucket: str,
    key: str,
    table_name: str,
    region: str = "eu-west-2",
    aws_access_key_id: str | None = None,
    aws_secret_access_key: str | None = None,
    file_format: str = "parquet",
) -> int:
    """Ingest an S3 dataset into ``bronze.<table_name>``.

    Args:
        file_format: ``parquet`` (default) or ``delta``.

    Returns the number of rows loaded.
    """
    log.info("Reading s3://%s/%s", bucket, key)

    reader = read_delta_from_s3 if file_format == "delta" else read_parquet_from_s3
    df = reader(bucket, key, region, aws_access_key_id, aws_secret_access_key)
    df = add_extract_metadata(df, f"s3://{bucket}")

    count = load_to_bronze(df, table_name)
    write_watermark(f"s3_{table_name}", utc_now_iso())
    log.info("Loaded %s rows from S3 into bronze.%s", f"{count:,}", table_name)
    return count
