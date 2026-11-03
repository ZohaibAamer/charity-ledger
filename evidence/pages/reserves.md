---
title: Reserves Analysis
---

# Reserves Analysis

```sql reserves_bands
select
    reserves_band,
    count(*) as charity_count,
    round(avg(reserves_months_cover), 1) as avg_months_cover,
    round(avg(reserves_to_spending_ratio), 2) as avg_ratio
from gold.charity_reserves_ratio
group by reserves_band
order by
    case reserves_band
        when 'negative' then 0
        when 'critically_low' then 1
        when 'low' then 2
        when 'adequate' then 3
        when 'healthy' then 4
        when 'high' then 5
    end
```

<BarChart
    data={reserves_bands}
    x=reserves_band
    y=charity_count
    title="Charities by Reserves Band"
/>

<DataTable
    data={reserves_bands}
/>

## Critically Low Reserves

```sql critical_reserves
select
    charity_number,
    total_income,
    total_spending,
    reserves,
    reserves_to_spending_ratio,
    reserves_months_cover
from gold.charity_reserves_ratio
where reserves_band = 'critically_low'
order by reserves_to_spending_ratio asc
limit 30
```

<DataTable
    data={critical_reserves}
    search=true
/>
