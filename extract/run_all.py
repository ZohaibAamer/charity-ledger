"""Run all extractors in sequence.

API sources always run. Cloud storage sources (ADLS, S3, Snowflake)
run only when their credentials are configured in the environment.
"""
from extract import charity_commission, companies_house, config, grantnav


def _run_cloud_sources() -> None:
    ran_any = False

    if config.ADLS_STORAGE_ACCOUNT:
        from extract.connectors.adls import ingest_from_adls

        print("\n[cloud] ADLS Gen2")
        ingest_from_adls(
            storage_account=config.ADLS_STORAGE_ACCOUNT,
            container=config.ADLS_CONTAINER,
            path="charity_commission/",
            table_name="adls_charity_data",
            credential=config.ADLS_CREDENTIAL or None,
        )
        ran_any = True

    if config.S3_BUCKET:
        from extract.connectors.s3 import ingest_from_s3

        print("\n[cloud] Amazon S3")
        ingest_from_s3(
            bucket=config.S3_BUCKET,
            key="companies_house/",
            table_name="s3_company_data",
            region=config.S3_REGION,
            aws_access_key_id=config.AWS_ACCESS_KEY_ID or None,
            aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY or None,
        )
        ran_any = True

    if config.SNOWFLAKE_ACCOUNT:
        from extract.connectors.snowflake import ingest_from_snowflake

        print("\n[cloud] Snowflake")
        ingest_from_snowflake(
            account=config.SNOWFLAKE_ACCOUNT,
            user=config.SNOWFLAKE_USER,
            password=config.SNOWFLAKE_PASSWORD,
            database=config.SNOWFLAKE_DATABASE,
            schema=config.SNOWFLAKE_SCHEMA,
            table="GRANTS",
            target_table="sf_grants",
            warehouse=config.SNOWFLAKE_WAREHOUSE,
            role=config.SNOWFLAKE_ROLE or None,
            watermark_column="LAST_MODIFIED",
        )
        ran_any = True

    if not ran_any:
        print("\n[cloud] No cloud storage credentials configured; skipping")


def main():
    print("=" * 60)
    print("CHARITY LEDGER - EXTRACTION PIPELINE")
    print("=" * 60)

    print("\n[1/3] Charity Commission")
    charity_commission.run()

    print("\n[2/3] Companies House")
    companies_house.run()

    print("\n[3/3] 360Giving GrantNav")
    grantnav.run()

    _run_cloud_sources()

    print("\n" + "=" * 60)
    print("All extractions complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
