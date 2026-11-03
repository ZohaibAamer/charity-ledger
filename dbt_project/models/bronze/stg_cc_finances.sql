with source as (
    select * from {{ source('bronze', 'cc_finances') }}
)

select
    cast("regno" as varchar)                         as charity_number,
    cast("fystart" as varchar)                       as financial_year_start,
    cast("fyend" as varchar)                         as financial_year_end,
    cast("income" as double)                         as total_income,
    cast("spending" as double)                       as total_spending,
    cast("reserves" as double)                       as reserves,
    cast("invest" as double)                         as investments,
    cast("funds_end" as double)                      as total_funds_end,
    cast("funds_restrict" as double)                 as restricted_funds,
    cast("funds_unrestrict" as double)               as unrestricted_funds,
    cast("funds_endow" as double)                    as endowment_funds,
    cast("employees" as integer)                     as employee_count,
    cast("volunteers" as integer)                    as volunteer_count,
    "_extracted_at",
    "_source"
from source
