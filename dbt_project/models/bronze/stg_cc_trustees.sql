with source as (
    select * from {{ source('bronze', 'cc_trustees') }}
)

select
    cast(registered_charity_number as varchar) as charity_number,
    trustee_name,
    cast(individual_id as varchar) as trustee_id,
    trustee_is_chair as is_chair,
    cast(trustee_date_of_appointment as varchar) as appointment_date,
    _extracted_at,
    _source
from source
