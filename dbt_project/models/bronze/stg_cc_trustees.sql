with source as (
    select * from {{ source('bronze', 'cc_trustees') }}
)

select
    cast("regno" as varchar)                         as charity_number,
    "trustee_name"                                   as trustee_name,
    cast("trustee_id" as varchar)                    as trustee_id,
    "trustee_is_chair"                               as is_chair,
    cast("date_of_appointment" as varchar)           as appointment_date,
    "_extracted_at",
    "_source"
from source
