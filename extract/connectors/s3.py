"""Amazon S3 connector.

Reads Parquet and Delta tables from S3 buckets using
AWS credentials or IAM roles.
"""
from datetime import datetime

import polars as pl

from extract.loader import load_to_bronze, write_watermark


def read_parquet_from_s3(
    bucket: str,
    key: str,
    region: str = "eu-west-2",
    aws_access_key_id: str | None = None,
    aws_secret_access_key: str | None = None,
) -> pl.DataFrame:
    """Read a Parquet file or prefix from S3."""
    storage_options = {"aws_region": region}
    if aws_access_key_id and aws_secret_access_key:
        storage_options["aws_access_key_id"] = aws_access_key_id
        storage_options["aws_secret_access_key"] = aws_secret_access_key

    uri = f"s3://{bucket}/{key}"
    return pl.read_parquet(uri, storage_options=storage_options)


def read_delta_from_s3(
    bucket: str,
    key: str,
    region: str = "eu-west-2",
    aws_access_key_id: str | None = None,
    aws_secret_access_key: str | None = None,
) -> pl.DataFrame:
    """Read a Delta Lake table from S3."""
    storage_options = {"aws_region": region}
    if aws_access_key_id and aws_secret_access_key:
        storage_options["aws_access_key_id"] = aws_access_key_id
        storage_options["aws_secret_access_key"] = aws_secret_access_key

    uri = f"s3://{bucket}/{key}"
    return pl.read_delta(uri, storage_options=storage_options)


def ingest_from_s3(
    bucket: str,
    key: str,
    table_name: str,
    region: str = "eu-west-2",
    aws_access_key_id: str | None = None,
    aws_secret_access_key: str | None = None,
    file_format: str = "parquet",
) -> int:
    """Ingest data from S3 into a bronze table."""
    print(f"Reading from s3://{bucket}/{key}...")

    if file_format == "delta":
        df = read_delta_from_s3(
            bucket, key, region, aws_access_key_id, aws_secret_access_key
        )
    else:
        df = read_parquet_from_s3(
            bucket, key, region, aws_access_key_id, aws_secret_access_key
        )

    df = df.with_columns(
        pl.lit(datetime.utcnow().isoformat()).alias("_extracted_at"),
        pl.lit(f"s3://{bucket}").alias("_source"),
    )

    count = load_to_bronze(df, table_name)
    write_watermark(f"s3_{table_name}", datetime.utcnow().isoformat())
    print(f"Loaded {count:,} rows from S3 into {table_name}")
    return count
