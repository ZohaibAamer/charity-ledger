{{
    config(
        materialized='table',
        schema='silver'
    )
}}

with charities as (
    select * from {{ ref('stg_cc_charities') }}
),

companies as (
    select * from {{ ref('stg_ch_companies') }}
),

grants as (
    select * from {{ ref('stg_gn_grants') }}
),

-- Match charities to companies via charity number in company name or SIC codes
charity_company_match as (
    select
        c.charity_number,
        c.charity_name,
        co.company_number,
        co.company_name,
        case
            when lower(co.company_name) = lower(c.charity_name)
                then 1.0
            when lower(co.company_name) like '%' || lower(c.charity_name) || '%'
                then 0.8
            when co.sic_code_1 like '%charity%' or co.sic_code_1 like '%74990%'
                then 0.5
            else 0.3
        end as match_confidence,
        case
            when lower(co.company_name) = lower(c.charity_name)
                then 'exact_name'
            when lower(co.company_name) like '%' || lower(c.charity_name) || '%'
                then 'partial_name'
            when co.sic_code_1 like '%charity%' or co.sic_code_1 like '%74990%'
                then 'sic_code'
            else 'fuzzy'
        end as match_method
    from charities c
    inner join companies co
        on lower(replace(co.company_name, ' ', ''))
            = lower(replace(c.charity_name, ' ', ''))
        or (co.company_number is not null
            and length(co.company_number) > 0)
    where co.company_status != 'Dissolved'
),

-- Match grants to charities via charity number
grant_charity_match as (
    select
        g.grant_id,
        g.recipient_charity_number as charity_number,
        g.recipient_company_number as company_number,
        g.recipient_org_name,
        case
            when g.recipient_charity_number is not null
                and length(g.recipient_charity_number) > 0
                then 1.0
            when g.recipient_company_number is not null
                and length(g.recipient_company_number) > 0
                then 0.9
            else 0.4
        end as match_confidence,
        case
            when g.recipient_charity_number is not null
                and length(g.recipient_charity_number) > 0
                then 'charity_number'
            when g.recipient_company_number is not null
                and length(g.recipient_company_number) > 0
                then 'company_number'
            else 'name_only'
        end as match_method
    from grants g
    where g.recipient_charity_number is not null
       or g.recipient_company_number is not null
       or g.recipient_org_name is not null
),

-- Build unified entity map
entity_map as (
    select
        c.charity_number,
        c.charity_name,
        ccm.company_number,
        ccm.company_name,
        ccm.match_confidence as company_match_confidence,
        ccm.match_method as company_match_method,
        count(distinct gcm.grant_id) as grant_count,
        max(gcm.match_confidence) as best_grant_match_confidence
    from charities c
    left join charity_company_match ccm
        on c.charity_number = ccm.charity_number
    left join grant_charity_match gcm
        on c.charity_number = gcm.charity_number
    where c.subsidiary_number = 0
    group by
        c.charity_number,
        c.charity_name,
        ccm.company_number,
        ccm.company_name,
        ccm.match_confidence,
        ccm.match_method
)

select
    {{ dbt_utils.generate_surrogate_key(['charity_number', 'company_number']) }} as entity_id,
    charity_number,
    charity_name,
    company_number,
    company_name,
    company_match_confidence,
    company_match_method,
    grant_count,
    best_grant_match_confidence,
    current_timestamp as _loaded_at
from entity_map
