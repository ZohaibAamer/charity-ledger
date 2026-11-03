{{
    config(
        materialized='table',
        schema='silver'
    )
}}

with charities as (
    select * from {{ ref('stg_cc_charities') }}
    where subsidiary_number = 0
),

companies as (
    select * from {{ ref('stg_ch_companies') }}
    where company_status != 'Dissolved'
),

grants as (
    select * from {{ ref('stg_gn_grants') }}
),

-- Match charities to companies via normalized name
charity_company_match as (
    select
        c.charity_number,
        c.charity_name,
        co.company_number,
        co.company_name,
        case
            when lower(co.company_name) = lower(c.charity_name)
                then 1.0
            when
                lower(replace(co.company_name, ' ', ''))
                = lower(replace(c.charity_name, ' ', ''))
                then 0.9
            else 0.7
        end as match_confidence,
        case
            when lower(co.company_name) = lower(c.charity_name)
                then 'exact_name'
            when
                lower(replace(co.company_name, ' ', ''))
                = lower(replace(c.charity_name, ' ', ''))
                then 'normalized_name'
            else 'other'
        end as match_method
    from charities as c
    inner join companies as co
        on
            lower(replace(co.company_name, ' ', ''))
            = lower(replace(c.charity_name, ' ', ''))
),

-- Deduplicate: keep the best company match per charity
best_company_match as (
    select *
    from (
        select
            *,
            row_number() over (
                partition by charity_number
                order by match_confidence desc, company_number asc
            ) as rn
        from charity_company_match
    )
    where rn = 1
),

-- Count grants per charity
grant_counts as (
    select
        recipient_charity_number as charity_number,
        count(distinct grant_id) as grant_count,
        max(case
            when recipient_charity_number is not null then 1.0
            when recipient_company_number is not null then 0.9
            else 0.4
        end) as best_grant_match_confidence
    from grants
    where recipient_charity_number is not null
    group by recipient_charity_number
)

select
    {{ dbt_utils.generate_surrogate_key(['c.charity_number']) }} as entity_id,
    c.charity_number,
    c.charity_name,
    bcm.company_number,
    bcm.company_name,
    bcm.match_confidence as company_match_confidence,
    bcm.match_method as company_match_method,
    coalesce(gc.grant_count, 0) as grant_count,
    gc.best_grant_match_confidence,
    current_timestamp as _loaded_at
from charities as c
left join best_company_match as bcm
    on c.charity_number = bcm.charity_number
left join grant_counts as gc
    on c.charity_number = gc.charity_number
