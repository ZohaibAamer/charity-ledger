# UK Charity Financial Health Warehouse

[![CI](https://github.com/ZohaibAamer/charity-ledger/actions/workflows/ci.yml/badge.svg)](https://github.com/ZohaibAamer/charity-ledger/actions/workflows/ci.yml)
[![Pipeline](https://github.com/ZohaibAamer/charity-ledger/actions/workflows/daily_pipeline.yml/badge.svg)](https://github.com/ZohaibAamer/charity-ledger/actions/workflows/daily_pipeline.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![dbt](https://img.shields.io/badge/dbt-duckdb-orange.svg)](https://github.com/duckdb/dbt-duckdb)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> A production-style data warehouse that consolidates UK charity register data, Companies House filings, and 360Giving grant records into a unified **health scorecard** for funders and consultants.

**Problem:** Funders and consultants can't see a charity's full picture because register data, company filings and grant history sit in separate systems with no shared keys.

**Solution:** Medallion architecture with entity resolution, SCD2 history tracking, and a composite health score — reading from **ADLS**, **S3**, and **Snowflake**.

---

## Architecture

```
+--------------------------------------------------------------------+
|                            DATA SOURCES                            |
|    +----------+   +-----------+   +----------+   +-----------+     |
|    |   ADLS   |   | Snowflake |   |    S3    |   | REST APIs |     |
|    +-----+----+   +-----+-----+   +-----+----+   +-----+-----+     |
+----------|--------------|---------------|--------------|-----------+
           v              v               v              v
+--------------------------------------------------------------------+
|  EXTRACT  (Python, Polars, httpx)                                  |
|  - Cloud connectors: ADLS Gen2, S3, Snowflake                      |
|  - Incremental loads with watermark tracking                       |
|  - Scheduled every 6 hours via GitHub Actions                      |
+---------------------------------+----------------------------------+
                                  v
+--------------------------------------------------------------------+
|  BRONZE  (dbt-duckdb)                                              |
|  - Charity Commission register, finances, trustees                 |
|  - Companies House bulk data + API profiles                        |
|  - 360Giving GrantNav grant records                                |
+---------------------------------+----------------------------------+
                                  v
+--------------------------------------------------------------------+
|  SILVER  (dbt-duckdb)                                              |
|  - Entity resolution: charity <-> company <-> grant recipient      |
|  - Match confidence scores (exact / normalized name)               |
|  - SCD2 history on trustees and finances                           |
+---------------------------------+----------------------------------+
                                  v
+--------------------------------------------------------------------+
|  GOLD  (dbt-duckdb)                                                |
|  - Income trend (YoY growth)                                       |
|  - Reserves ratio (months cover, risk banding)                     |
|  - Grant dependency (funder concentration)                         |
|  - Filing timeliness (overdue detection)                           |
|  - Health scorecard (0-100 composite)                              |
+---------------------------------+----------------------------------+
                                  v
+--------------------------------------------------------------------+
|  DASHBOARD  (Evidence.dev)                                         |
|  Scorecard | Income | Reserves | Grants | Filings | Quality        |
+--------------------------------------------------------------------+
```

## Data Sources & Connectors

| Source | Connector | Format | Frequency |
|--------|-----------|--------|-----------|
| Charity Commission | ADLS / REST API | Parquet / ZIP | Every 6h |
| Companies House | S3 / REST API | Parquet / JSON | Every 6h |
| 360Giving GrantNav | Snowflake / REST | Delta / JSON | Every 6h |
| Custom sources | ADLS, S3, Snowflake | Parquet, Delta | Configurable |

### Supported Storage Backends

- **Azure Data Lake Storage Gen2** — Parquet and Delta Lake tables via `adlfs`
- **Amazon S3** — Parquet and Delta Lake tables via `s3fs`
- **Snowflake** — Full table reads and incremental queries via `connectorx`

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Extract** | Python 3.11+, Polars, httpx, adlfs, s3fs, connectorx |
| **Transform** | dbt-core, dbt-duckdb, dbt_utils |
| **Store** | DuckDB |
| **Orchestrate** | GitHub Actions (every 6 hours) |
| **Dashboard** | Evidence.dev |
| **Data Quality** | dbt tests, data contracts, freshness checks |

## Quick Start

```bash
# Install dependencies
pip install -e ".[snowflake,azure,aws]"

# Configure credentials
cp .env.example .env
# Edit .env with your ADLS/S3/Snowflake credentials

# Run extractions
python -m extract.run_all

# Run dbt
cd dbt_project
dbt deps
dbt build --profiles-dir .
dbt test --profiles-dir .

# Generate quality report
dbt run-operation generate_data_quality_report --profiles-dir .

# Start dashboard
cd ../evidence
npm install
npm run dev
```

## Key Features

- **Multi-source ingestion** from ADLS Gen2, S3, and Snowflake — no CSV files
- **Medallion architecture** (bronze → silver → gold) with clear data contracts per layer
- **Entity resolution** linking charity ↔ company ↔ grant recipient with match confidence scores
- **SCD2 history** tracking changes to trustees and financial data over time
- **Incremental loads** with watermark tracking for efficient scheduled updates
- **Data contracts** defining required columns, freshness SLAs, and constraints
- **Data quality report** published on every pipeline run
- **Health scorecard** (0-100) combining income stability, reserves, funder diversification, and filing compliance

## Health Score Methodology

The composite health score (0-100) weights four dimensions equally:

| Dimension | Points | Signals |
|-----------|--------|---------|
| Income Stability | 0-25 | Year-over-year growth rate |
| Reserves Health | 0-25 | Months of spending cover |
| Funder Diversification | 0-25 | Number of unique funders |
| Filing Compliance | 0-25 | Companies House due dates |

## Configuration

Copy `.env.example` to `.env` and configure your storage backends:

```bash
# At least one storage backend is required
ADLS_STORAGE_ACCOUNT=your_account    # Azure Data Lake
S3_BUCKET=your-bucket                 # Amazon S3
SNOWFLAKE_ACCOUNT=your_account        # Snowflake

# Optional: Companies House API for enrichment
COMPANIES_HOUSE_API_KEY=your_key
```

## Project Structure

```
charity-ledger/
├── extract/                    # Python extraction layer
│   ├── connectors/             # Cloud storage connectors
│   │   ├── adls.py             # Azure Data Lake Storage Gen2
│   │   ├── s3.py               # Amazon S3
│   │   └── snowflake.py        # Snowflake
│   ├── charity_commission.py   # Charity Commission extractor
│   ├── companies_house.py      # Companies House extractor
│   ├── grantnav.py             # 360Giving GrantNav extractor
│   ├── config.py               # Configuration and env vars
│   ├── loader.py               # DuckDB loader + watermarks
│   └── run_all.py              # Pipeline orchestrator
├── dbt_project/                # dbt transformation layer
│   ├── models/
│   │   ├── bronze/             # Raw staging views
│   │   ├── silver/             # Entity resolution, SCD2
│   │   └── gold/               # Scorecard, trends, ratios
│   ├── tests/                  # Data integrity assertions
│   └── macros/                 # Quality report, freshness
├── contracts/                  # Data contracts per layer
├── evidence/                   # Evidence.dev dashboard
│   └── pages/                  # Dashboard pages
├── .github/workflows/          # CI/CD pipeline (6h schedule)
└── pyproject.toml              # Dependencies
```

## Dashboard Pages

| Page | Description |
|------|-------------|
| **Scorecard** | Health score distribution, top/bottom charities |
| **Income Trends** | Year-over-year growth analysis, surplus/deficit |
| **Reserves** | Reserves-to-spending ratio, risk banding |
| **Grant Dependency** | Funder concentration, grant reliance |
| **Filing Timeliness** | Companies House compliance monitoring |
| **Data Quality** | Source freshness, entity resolution quality, coverage |

## License

MIT
