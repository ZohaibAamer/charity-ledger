---
title: Income Trends
---

# Income Trends

```sql income_growth
select
    case
        when income_growth_pct >= 25 then 'Strong growth (>25%)'
        when income_growth_pct >= 10 then 'Growth (10-25%)'
        when income_growth_pct >= 0 then 'Stable (0-10%)'
        when income_growth_pct >= -10 then 'Slight decline (-10-0%)'
        when income_growth_pct >= -25 then 'Decline (-25 to -10%)'
        else 'Severe decline (<-25%)'
    end as growth_band,
    count(*) as charity_count
from gold.charity_income_trend
where recency_rank = 1
  and income_growth_pct is not null
group by 1
order by min(income_growth_pct)
```

<BarChart
    data={income_growth}
    x=growth_band
    y=charity_count
    title="Year-over-Year Income Growth Distribution"
/>

## Income vs Expenditure

```sql income_vs_spend
select
    charity_number,
    financial_year_end,
    total_income,
    total_spending,
    surplus_deficit,
    income_growth_pct
from gold.charity_income_trend
where recency_rank <= 5
order by total_income desc
limit 100
```

<DataTable
    data={income_vs_spend}
    search=true
/>

## Largest Surpluses and Deficits

```sql surplus_deficit
select
    charity_number,
    financial_year_end,
    total_income,
    total_spending,
    surplus_deficit
from gold.charity_income_trend
where recency_rank = 1
  and surplus_deficit is not null
order by abs(surplus_deficit) desc
limit 20
```

<DataTable
    data={surplus_deficit}
    search=true
/>
