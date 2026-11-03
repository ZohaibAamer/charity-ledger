{{
    config(
        materialized='table',
        schema='gold'
    )
}}

with latest_finances as (
    select
        charity_number,
        financial_year_end,
        total_income,
        total_spending,
        reserves,
        unrestricted_funds,
        total_funds_end,
        row_number() over (
            partition by charity_number
            order by financial_year_end desc
        ) as rn
    from {{ ref('scd2_finances') }}
    where is_current = true
      and total_spending is not null
      and total_spending > 0
)

select
    charity_number,
    financial_year_end,
    total_income,
    total_spending,
    reserves,
    unrestricted_funds,
    total_funds_end,
    round(reserves / total_spending, 2) as reserves_to_spending_ratio,
    round(reserves / total_spending * 12, 1) as reserves_months_cover,
    case
        when reserves / total_spending < 0.25 then 'critically_low'
        when reserves / total_spending < 0.5 then 'low'
        when reserves / total_spending < 1.0 then 'adequate'
        when reserves / total_spending < 2.0 then 'healthy'
        else 'high'
    end as reserves_band,
    current_timestamp as _loaded_at
from latest_finances
where rn = 1
  and reserves is not null
