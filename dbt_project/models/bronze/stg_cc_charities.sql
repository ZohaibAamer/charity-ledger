with source as (
    select * from {{ source('bronze', 'cc_charities') }}
)

select
    cast("registered_charity_number" as varchar)     as charity_number,
    cast("linked_charity_number" as integer)         as subsidiary_number,
    "charity_name"                                   as charity_name,
    "charity_type"                                   as organisation_type,
    "charity_activities"                              as activities,
    "charity_objects"                                 as objects,
    "charity_governing_document"                     as governing_document,
    cast("date_of_registration" as varchar)          as registration_date,
    cast("date_of_removal" as varchar)               as removal_date,
    "charity_registration_status"                    as registration_status,
    cast("latest_income" as double)                  as latest_income,
    cast("latest_expenditure" as double)             as latest_expenditure,
    "_extracted_at",
    "_source"
from source
