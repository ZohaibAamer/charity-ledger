{{
    config(
        materialized='table',
        schema='gold'
    )
}}

with finances as (
    select * from {{ ref('scd2_finances') }}
    where is_current = true
),

yearly as (
    select
        charity_number,
        financial_year_end,
        total_income,
        total_spending,
        total_income - total_spending as surplus_deficit,
        lag(total_income) over (
            partition by charity_number
            order by financial_year_end
        ) as prev_year_income,
        row_number() over (
            partition by charity_number
            order by financial_year_end desc
        ) as recency_rank
    from finances
    where total_income is not null
)

select
    charity_number,
    financial_year_end,
    total_income,
    total_spending,
    surplus_deficit,
    prev_year_income,
    case
        when prev_year_income is not null and prev_year_income > 0
            then round((total_income - prev_year_income) / prev_year_income * 100, 1)
    end as income_growth_pct,
    recency_rank,
    current_timestamp as _loaded_at
from yearly
