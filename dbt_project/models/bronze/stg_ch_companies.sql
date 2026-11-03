with source as (
    select * from {{ source('bronze', 'ch_companies') }}
)

select
    source.companynumber as company_number,
    source.companyname as company_name,
    source.companycategory as company_category,
    source.companystatus as company_status,
    source.countryoforigin as country_of_origin,
    cast(source.incorporationdate as varchar) as incorporation_date,
    cast(source.dissolutiondate as varchar) as dissolution_date,
    "RegAddress.AddressLine1" as address_line_1,
    "RegAddress.PostTown" as post_town,
    "RegAddress.PostCode" as post_code,
    "SICCode.SicText_1" as sic_code_1,
    "SICCode.SicText_2" as sic_code_2,
    "Accounts.AccountCategory" as accounts_category,
    cast("Accounts.NextDueDate" as varchar) as accounts_next_due,
    cast("Returns.NextDueDate" as varchar) as returns_next_due,
    source._extracted_at,
    source._source
from source
