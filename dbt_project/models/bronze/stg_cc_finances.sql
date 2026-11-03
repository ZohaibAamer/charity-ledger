with source as (
    select * from {{ source('bronze', 'cc_finances') }}
)

select
    cast(registered_charity_number as varchar) as charity_number,
    cast(fin_period_start_date as date) as financial_year_start,
    cast(fin_period_end_date as date) as financial_year_end,
    cast(total_gross_income as double) as total_income,
    cast(total_gross_expenditure as double) as total_spending,
    cast(charity_reserves as double) as reserves,
    cast(total_investments as double) as investments,
    cast(total_funds_end_of_period as double) as total_funds_end,
    cast(funds_restricted as double) as restricted_funds,
    cast(funds_unrestricted as double) as unrestricted_funds,
    cast(funds_endowment as double) as endowment_funds,
    cast(count_employees as integer) as employee_count,
    cast(count_volunteers as integer) as volunteer_count,
    _extracted_at,
    _source
from source
