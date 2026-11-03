with source as (
    select * from {{ source('bronze', 'gn_grants') }}
)

select
    "id"                                             as grant_id,
    "title"                                          as grant_title,
    "description"                                    as grant_description,
    "currency"                                       as currency,
    cast("amountAwarded" as double)                  as amount_awarded,
    cast("awardDate" as varchar)                     as award_date,
    "recipientOrganization_id"                       as recipient_org_id,
    "recipientOrganization_name"                     as recipient_org_name,
    "recipientOrganization_charityNumber"            as recipient_charity_number,
    "recipientOrganization_companyNumber"             as recipient_company_number,
    "fundingOrganization_id"                         as funder_org_id,
    "fundingOrganization_name"                       as funder_name,
    "grantProgramme_title"                           as programme_title,
    "_extracted_at",
    "_source"
from source
