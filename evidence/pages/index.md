---
title: Charity Health Scorecard
---

# UK Charity Financial Health Dashboard

```sql scorecard_summary
select
    count(*) as total_charities,
    round(avg(health_score), 1) as avg_health_score,
    count(case when health_score >= 75 then 1 end) as healthy,
    count(case when health_score >= 50 and health_score < 75 then 1 end) as moderate,
    count(case when health_score < 50 then 1 end) as at_risk
from gold.charity_health_scorecard
```

<BigValue
    data={scorecard_summary}
    value=total_charities
    title="Total Charities"
/>

<BigValue
    data={scorecard_summary}
    value=avg_health_score
    title="Avg Health Score"
    fmt="0.0"
/>

<BigValue
    data={scorecard_summary}
    value=healthy
    title="Healthy (75+)"
/>

<BigValue
    data={scorecard_summary}
    value=at_risk
    title="At Risk (<50)"
/>

## Health Score Distribution

```sql score_distribution
select
    case
        when health_score >= 90 then '90-100'
        when health_score >= 75 then '75-89'
        when health_score >= 60 then '60-74'
        when health_score >= 45 then '45-59'
        when health_score >= 30 then '30-44'
        else '0-29'
    end as score_band,
    count(*) as charity_count
from gold.charity_health_scorecard
group by 1
order by 1
```

<BarChart
    data={score_distribution}
    x=score_band
    y=charity_count
    title="Charities by Health Score Band"
/>

## Top 20 Healthiest Charities

```sql top_charities
select
    charity_number,
    charity_name,
    health_score,
    latest_income,
    reserves_band,
    funder_concentration,
    accounts_filing_status
from gold.charity_health_scorecard
order by health_score desc
limit 20
```

<DataTable
    data={top_charities}
    search=true
/>

## Bottom 20 At-Risk Charities

```sql bottom_charities
select
    charity_number,
    charity_name,
    health_score,
    latest_income,
    reserves_band,
    funder_concentration,
    accounts_filing_status
from gold.charity_health_scorecard
where health_score is not null
order by health_score asc
limit 20
```

<DataTable
    data={bottom_charities}
    search=true
/>
