{{
    config(
        materialized='table',
        schema='gold'
    )
}}

with charities as (
    select
        charity_number,
        charity_name,
        organisation_type,
        registration_date,
        removal_date,
        latest_income,
        latest_expenditure
    from {{ ref('stg_cc_charities') }}
    where subsidiary_number = 0
),

income as (
    select * from {{ ref('charity_income_trend') }}
    where recency_rank = 1
),

reserves as (
    select * from {{ ref('charity_reserves_ratio') }}
),

grants as (
    select * from {{ ref('charity_grant_dependency') }}
),

filings as (
    select * from {{ ref('charity_filing_timeliness') }}
),

entities as (
    select * from {{ ref('entity_resolution') }}
)

select
    c.charity_number,
    c.charity_name,
    c.organisation_type,
    c.registration_date,
    c.removal_date,
    e.company_number,
    e.company_match_confidence,

    -- Income
    c.latest_income,
    c.latest_expenditure,
    i.income_growth_pct,
    i.surplus_deficit,

    -- Reserves
    r.reserves,
    r.reserves_to_spending_ratio,
    r.reserves_months_cover,
    r.reserves_band,

    -- Grant dependency
    g.total_grants,
    g.unique_funders,
    g.total_grant_income,
    g.grant_dependency_pct,
    g.funder_concentration,

    -- Filing timeliness
    f.accounts_next_due,
    f.accounts_filing_status,
    f.returns_next_due,
    f.returns_filing_status,

    -- Overall health score (0-100)
    (
        -- Income stability (0-25)
        case
            when i.income_growth_pct is null then 12
            when i.income_growth_pct >= 10 then 25
            when i.income_growth_pct >= 0 then 20
            when i.income_growth_pct >= -10 then 15
            when i.income_growth_pct >= -25 then 10
            else 5
        end
        -- Reserves health (0-25)
        + case
            when r.reserves_band = 'high' then 20
            when r.reserves_band = 'healthy' then 25
            when r.reserves_band = 'adequate' then 20
            when r.reserves_band = 'low' then 10
            when r.reserves_band = 'critically_low' then 5
            else 12
        end
        -- Funder diversification (0-25)
        + case
            when g.funder_concentration = 'highly_diversified' then 25
            when g.funder_concentration = 'diversified' then 20
            when g.funder_concentration = 'concentrated' then 10
            when g.funder_concentration = 'single_funder' then 5
            else 15
        end
        -- Filing compliance (0-25)
        + case
            when f.accounts_filing_status = 'overdue'
              or f.returns_filing_status = 'overdue' then 5
            when f.accounts_filing_status = 'due_soon'
              or f.returns_filing_status = 'due_soon' then 15
            when f.accounts_filing_status = 'on_track'
              and f.returns_filing_status = 'on_track' then 25
            else 15
        end
    ) as health_score,

    current_timestamp as _loaded_at

from charities c
left join entities e on c.charity_number = e.charity_number
left join income i on c.charity_number = i.charity_number
left join reserves r on c.charity_number = r.charity_number
left join grants g on c.charity_number = g.charity_number
left join filings f on c.charity_number = f.charity_number
