{{
    config(
        materialized='table',
        schema='gold'
    )
}}

with grants as (
    select * from {{ ref('int_grants_enriched') }}
    where award_date is not null
),

latest_finances as (
    select
        charity_number,
        financial_year_end,
        total_income,
        row_number() over (
            partition by charity_number
            order by financial_year_end desc
        ) as rn
    from {{ ref('scd2_finances') }}
    where is_current = true
      and total_income is not null
      and total_income > 0
),

grant_summary as (
    select
        recipient_charity_number as charity_number,
        count(distinct grant_id) as total_grants,
        count(distinct funder_org_id) as unique_funders,
        sum(amount_awarded) as total_grant_income,
        min(award_date) as earliest_grant,
        max(award_date) as latest_grant,
        avg(amount_awarded) as avg_grant_size,
        max(amount_awarded) as largest_grant
    from grants
    where recipient_charity_number is not null
    group by recipient_charity_number
)

select
    gs.charity_number,
    gs.total_grants,
    gs.unique_funders,
    gs.total_grant_income,
    gs.earliest_grant,
    gs.latest_grant,
    round(gs.avg_grant_size, 0) as avg_grant_size,
    gs.largest_grant,
    lf.total_income,
    case
        when lf.total_income is not null and lf.total_income > 0
            then round(gs.total_grant_income / lf.total_income * 100, 1)
        else null
    end as grant_dependency_pct,
    case
        when gs.unique_funders = 1 then 'single_funder'
        when gs.unique_funders <= 3 then 'concentrated'
        when gs.unique_funders <= 10 then 'diversified'
        else 'highly_diversified'
    end as funder_concentration,
    current_timestamp as _loaded_at
from grant_summary gs
left join latest_finances lf
    on gs.charity_number = lf.charity_number
    and lf.rn = 1
