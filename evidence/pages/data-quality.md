---
title: Data Quality
---

# Data Quality Report

## Source Freshness

```sql bronze_freshness
select
    'cc_charities' as source_table,
    count(*) as row_count,
    max(_extracted_at) as last_extracted
from bronze.cc_charities
union all
select 'cc_finances', count(*), max(_extracted_at) from bronze.cc_finances
union all
select 'cc_trustees', count(*), max(_extracted_at) from bronze.cc_trustees
union all
select 'ch_companies', count(*), max(_extracted_at) from bronze.ch_companies
union all
select 'gn_grants', count(*), max(_extracted_at) from bronze.gn_grants
```

<DataTable
    data={bronze_freshness}
/>

## Entity Resolution Quality

```sql entity_quality
select
    company_match_method,
    count(*) as match_count,
    round(avg(company_match_confidence), 3) as avg_confidence,
    round(min(company_match_confidence), 3) as min_confidence
from silver.entity_resolution
where company_match_method is not null
group by company_match_method
order by avg_confidence desc
```

<BarChart
    data={entity_quality}
    x=company_match_method
    y=match_count
    title="Entity Matches by Method"
/>

<DataTable
    data={entity_quality}
/>

## Silver Layer Stats

```sql silver_stats
select
    'entity_resolution' as model,
    count(*) as rows,
    count(distinct charity_number) as unique_charities,
    count(company_number) as with_company
from silver.entity_resolution
union all
select
    'scd2_trustees',
    count(*),
    count(distinct charity_number),
    count(case when is_current then 1 end)
from silver.scd2_trustees
union all
select
    'scd2_finances',
    count(*),
    count(distinct charity_number),
    count(case when is_current then 1 end)
from silver.scd2_finances
```

<DataTable
    data={silver_stats}
/>

## Gold Layer Coverage

```sql gold_coverage
select
    (select count(*) from gold.charity_health_scorecard) as scorecards,
    (select count(*) from gold.charity_income_trend where recency_rank = 1) as with_income_trend,
    (select count(*) from gold.charity_reserves_ratio) as with_reserves,
    (select count(*) from gold.charity_grant_dependency) as with_grants,
    (select count(*) from gold.charity_filing_timeliness) as with_filing_data
```

<BigValue data={gold_coverage} value=scorecards title="Total Scorecards" />
<BigValue data={gold_coverage} value=with_income_trend title="With Income Data" />
<BigValue data={gold_coverage} value=with_reserves title="With Reserves" />
<BigValue data={gold_coverage} value=with_grants title="With Grant Data" />
<BigValue data={gold_coverage} value=with_filing_data title="With Filing Data" />
