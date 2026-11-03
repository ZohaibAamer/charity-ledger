with source as (
    select * from {{ source('bronze', 'ch_companies') }}
)

select
    "CompanyNumber"                                  as company_number,
    "CompanyName"                                    as company_name,
    "CompanyCategory"                                as company_category,
    "CompanyStatus"                                  as company_status,
    "CountryOfOrigin"                                as country_of_origin,
    cast("IncorporationDate" as varchar)             as incorporation_date,
    cast("DissolutionDate" as varchar)               as dissolution_date,
    "RegAddress.AddressLine1"                        as address_line_1,
    "RegAddress.PostTown"                            as post_town,
    "RegAddress.PostCode"                            as post_code,
    "SICCode.SicText_1"                              as sic_code_1,
    "SICCode.SicText_2"                              as sic_code_2,
    "Accounts.AccountCategory"                       as accounts_category,
    cast("Accounts.NextDueDate" as varchar)          as accounts_next_due,
    cast("Returns.NextDueDate" as varchar)           as returns_next_due,
    "_extracted_at",
    "_source"
from source
