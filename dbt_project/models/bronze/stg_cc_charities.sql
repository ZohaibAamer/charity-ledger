with source as (
    select * from {{ source('bronze', 'cc_charities') }}
)

select
    cast("regno" as varchar)                         as charity_number,
    cast("subno" as integer)                         as subsidiary_number,
    "name"                                           as charity_name,
    "orgtype"                                        as organisation_type,
    "aession"                                        as activities,
    "gd"                                             as governing_document,
    "aession"                                        as objects,
    cast("regy" as varchar)                          as registration_date,
    cast("rmd" as varchar)                           as removal_date,
    "remcode"                                        as removal_reason,
    cast("fyend" as varchar)                         as financial_year_end,
    cast("welsh" as boolean)                         as is_welsh,
    cast("incomelatestfinan" as double)              as latest_income,
    cast("expendlatestfinan" as double)              as latest_expenditure,
    "_extracted_at",
    "_source"
from source
