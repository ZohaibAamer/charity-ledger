{{
    config(
        materialized='table',
        schema='silver'
    )
}}

with grants as (
    select * from {{ ref('stg_gn_grants') }}
),

entities as (
    select * from {{ ref('entity_resolution') }}
)

select
    g.grant_id,
    g.grant_title,
    g.grant_description,
    g.currency,
    g.amount_awarded,
    try_cast(g.award_date as date) as award_date,
    try_cast(g.planned_start_date as date) as planned_start_date,
    try_cast(g.planned_end_date as date) as planned_end_date,
    g.recipient_org_id,
    g.recipient_org_name,
    g.recipient_charity_number,
    g.recipient_company_number,
    g.funder_org_id,
    g.funder_name,
    g.programme_title,
    e.entity_id,
    e.charity_name as matched_charity_name,
    e.company_number as matched_company_number,
    e.best_grant_match_confidence,
    current_timestamp as _loaded_at
from grants g
left join entities e
    on g.recipient_charity_number = e.charity_number
