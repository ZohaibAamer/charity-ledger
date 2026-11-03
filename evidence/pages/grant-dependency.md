---
title: Grant Dependency
---

# Grant Dependency Analysis

```sql funder_concentration
select
    funder_concentration,
    count(*) as charity_count,
    round(avg(grant_dependency_pct), 1) as avg_grant_dependency_pct,
    round(avg(total_grants), 0) as avg_grants,
    round(avg(total_grant_income), 0) as avg_grant_income
from gold.charity_grant_dependency
group by funder_concentration
order by
    case funder_concentration
        when 'single_funder' then 1
        when 'concentrated' then 2
        when 'diversified' then 3
        when 'highly_diversified' then 4
    end
```

<BarChart
    data={funder_concentration}
    x=funder_concentration
    y=charity_count
    title="Funder Concentration Distribution"
/>

<DataTable
    data={funder_concentration}
/>

## Most Grant-Dependent Charities

```sql high_dependency
select
    charity_number,
    total_grants,
    unique_funders,
    total_grant_income,
    total_income,
    grant_dependency_pct,
    funder_concentration
from gold.charity_grant_dependency
where grant_dependency_pct is not null
order by grant_dependency_pct desc
limit 30
```

<DataTable
    data={high_dependency}
    search=true
/>

## Largest Grant Recipients

```sql largest_recipients
select
    charity_number,
    total_grants,
    unique_funders,
    total_grant_income,
    avg_grant_size,
    largest_grant,
    earliest_grant,
    latest_grant
from gold.charity_grant_dependency
order by total_grant_income desc
limit 30
```

<DataTable
    data={largest_recipients}
    search=true
/>
