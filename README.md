# UK Charity Financial Health Warehouse

A data warehouse that consolidates UK charity register data, Companies House filings, and 360Giving grant records into a unified health scorecard for funders and consultants.

## Architecture

**Medallion layers** (bronze → silver → gold) built with dbt-duckdb:

- **Bronze**: Raw extracts from Charity Commission, Companies House, and GrantNav
- **Silver**: Entity resolution (charity ↔ company ↔ grant recipient with match confidence), SCD2 history on trustees and finances
- **Gold**: Charity health scorecard — income trend, reserves ratio, grant dependency, filing timeliness

## Data Sources

| Source | Method | Frequency |
|--------|--------|-----------|
| Charity Commission | Bulk ZIP extract | Daily |
| Companies House | Bulk CSV + REST API | Weekly |
| 360Giving GrantNav | Bulk JSON/CSV | Weekly |

## Stack

- **Extract**: Python, Polars, httpx
- **Transform**: dbt-duckdb with dbt_utils
- **Store**: DuckDB
- **Orchestrate**: GitHub Actions (daily at 6am UTC)
- **Dashboard**: Evidence.dev

## Quick Start

```bash
# Install dependencies
pip install -e .

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

- **Entity resolution** linking charity ↔ company ↔ grant recipient with match confidence scores
- **SCD2 history** tracking changes to trustees and financial data over time
- **Incremental loads** with watermark tracking for efficient daily updates
- **Data contracts** defining required columns, freshness SLAs, and constraints per layer
- **Data quality report** published on every pipeline run
- **Health scorecard** (0-100) combining income stability, reserves, funder diversification, and filing compliance

## Configuration

Copy `.env.example` to `.env` and set:

- `COMPANIES_HOUSE_API_KEY`: Free API key from [Companies House Developer Hub](https://developer.company-information.service.gov.uk/)

## Dashboard Pages

- **Scorecard**: Overall health score distribution with top/bottom charities
- **Income Trends**: Year-over-year growth analysis
- **Reserves**: Reserves-to-spending ratio and risk banding
- **Grant Dependency**: Funder concentration and grant reliance
- **Filing Timeliness**: Companies House filing compliance
- **Data Quality**: Source freshness, entity resolution quality, coverage stats
