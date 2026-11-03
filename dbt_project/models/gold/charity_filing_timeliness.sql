{{
    config(
        materialized='table',
        schema='gold'
    )
}}

with companies as (
    select * from {{ ref('stg_ch_companies') }}
),

entities as (
    select * from {{ ref('entity_resolution') }}
    where company_number is not null
),

charities as (
    select * from {{ ref('stg_cc_charities') }}
    where subsidiary_number = 0
)

select
    e.entity_id,
    e.charity_number,
    e.charity_name,
    e.company_number,
    c.registration_date,
    try_cast(co.accounts_next_due as date) as accounts_next_due,
    try_cast(co.returns_next_due as date) as returns_next_due,
    case
        when try_cast(co.accounts_next_due as date) < current_date
            then 'overdue'
        when try_cast(co.accounts_next_due as date) < current_date + interval '30' day
            then 'due_soon'
        else 'on_track'
    end as accounts_filing_status,
    case
        when try_cast(co.returns_next_due as date) < current_date
            then 'overdue'
        when try_cast(co.returns_next_due as date) < current_date + interval '30' day
            then 'due_soon'
        else 'on_track'
    end as returns_filing_status,
    co.company_status,
    co.accounts_category,
    current_timestamp as _loaded_at
from entities e
inner join companies co
    on e.company_number = co.company_number
inner join charities c
    on e.charity_number = c.charity_number
