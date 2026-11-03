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
        trustee_id,
        trustee_name,
        is_chair,
        appointment_date,
        _extracted_at
    from {{ ref('stg_cc_trustees') }}
),

{% if is_incremental() %}

existing as (
    select * from {{ this }}
    where is_current = true
),

changed as (
    select
        s.charity_number,
        s.trustee_id,
        s.trustee_name,
        s.is_chair,
        s.appointment_date,
        s._extracted_at
    from source s
    left join existing e
        on s.charity_number = e.charity_number
        and s.trustee_id = e.trustee_id
    where e.surrogate_key is null
        or s.trustee_name != e.trustee_name
        or coalesce(s.is_chair, 'N') != coalesce(e.is_chair, 'N')
),

-- Close out old records
expired as (
    select
        e.surrogate_key,
        e.charity_number,
        e.trustee_id,
        e.trustee_name,
        e.is_chair,
        e.appointment_date,
        e.valid_from,
        cast(current_timestamp as timestamp) as valid_to,
        false as is_current
    from existing e
    inner join changed c
        on e.charity_number = c.charity_number
        and e.trustee_id = c.trustee_id
),

-- New current records
new_current as (
    select
        {{ dbt_utils.generate_surrogate_key(['charity_number', 'trustee_id', '_extracted_at']) }} as surrogate_key,
        charity_number,
        trustee_id,
        trustee_name,
        is_chair,
        appointment_date,
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
    {{ dbt_utils.generate_surrogate_key(['charity_number', 'trustee_id', '_extracted_at']) }} as surrogate_key,
    charity_number,
    trustee_id,
    trustee_name,
    is_chair,
    appointment_date,
    cast(current_timestamp as timestamp) as valid_from,
    cast(null as timestamp) as valid_to,
    true as is_current
from source

{% endif %}
