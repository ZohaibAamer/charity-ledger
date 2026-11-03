---
title: Filing Timeliness
---

# Filing Timeliness

```sql filing_status
select
    accounts_filing_status,
    count(*) as charity_count
from gold.charity_filing_timeliness
group by accounts_filing_status
```

<BarChart
    data={filing_status}
    x=accounts_filing_status
    y=charity_count
    title="Accounts Filing Status"
/>

```sql returns_status
select
    returns_filing_status,
    count(*) as charity_count
from gold.charity_filing_timeliness
group by returns_filing_status
```

<BarChart
    data={returns_status}
    x=returns_filing_status
    y=charity_count
    title="Annual Returns Filing Status"
/>

## Overdue Filings

```sql overdue
select
    charity_number,
    charity_name,
    company_number,
    accounts_next_due,
    accounts_filing_status,
    returns_next_due,
    returns_filing_status,
    company_status
from gold.charity_filing_timeliness
where accounts_filing_status = 'overdue'
   or returns_filing_status = 'overdue'
order by accounts_next_due asc
```

<DataTable
    data={overdue}
    search=true
/>
