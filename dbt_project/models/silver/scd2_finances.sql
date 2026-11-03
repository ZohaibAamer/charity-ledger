{{
    config(
        materialized='incremental',
        unique_key='surrogate_key',
        schema='silver'
    )
}}

with source as (
    select
        charity_number,
        financial_year_start,
        financial_year_end,
        total_income,
        total_spending,
        reserves,
        investments,
        total_funds_end,
        restricted_funds,
        unrestricted_funds,
        endowment_funds,
        employee_count,
        volunteer_count,
        _extracted_at
    from {{ ref('stg_cc_finances') }}
),

{% if is_incremental() %}

existing as (
    select * from {{ this }}
    where is_current = true
),

changed as (
    select s.*
    from source s
    left join existing e
        on s.charity_number = e.charity_number
        and s.financial_year_end = e.financial_year_end
    where e.surrogate_key is null
        or s.total_income != e.total_income
        or s.total_spending != e.total_spending
        or s.reserves != e.reserves
),

expired as (
    select
        e.surrogate_key,
        e.charity_number,
        e.financial_year_start,
        e.financial_year_end,
        e.total_income,
        e.total_spending,
        e.reserves,
        e.investments,
        e.total_funds_end,
        e.restricted_funds,
        e.unrestricted_funds,
        e.endowment_funds,
        e.employee_count,
        e.volunteer_count,
        e.valid_from,
        cast(current_timestamp as timestamp) as valid_to,
        false as is_current
    from existing e
    inner join changed c
        on e.charity_number = c.charity_number
        and e.financial_year_end = c.financial_year_end
),

new_current as (
    select
        {{ dbt_utils.generate_surrogate_key(['charity_number', 'financial_year_end', '_extracted_at']) }} as surrogate_key,
        charity_number,
        financial_year_start,
        financial_year_end,
        total_income,
        total_spending,
        reserves,
        investments,
        total_funds_end,
        restricted_funds,
        unrestricted_funds,
        endowment_funds,
        employee_count,
        volunteer_count,
        cast(current_timestamp as timestamp) as valid_from,
        cast(null as timestamp) as valid_to,
        true as is_current
    from changed
)

select * from expired
union all
select * from new_current

{% else %}

select
    {{ dbt_utils.generate_surrogate_key(['charity_number', 'financial_year_end', '_extracted_at']) }} as surrogate_key,
    charity_number,
    financial_year_start,
    financial_year_end,
    total_income,
    total_spending,
    reserves,
    investments,
    total_funds_end,
    restricted_funds,
    unrestricted_funds,
    endowment_funds,
    employee_count,
    volunteer_count,
    cast(current_timestamp as timestamp) as valid_from,
    cast(null as timestamp) as valid_to,
    true as is_current
from source

{% endif %}
