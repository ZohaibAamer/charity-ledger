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
    cast("plannedDates.0.startDate" as varchar)      as planned_start_date,
    cast("plannedDates.0.endDate" as varchar)        as planned_end_date,
    "recipientOrganization.0.id"                     as recipient_org_id,
    "recipientOrganization.0.name"                   as recipient_org_name,
    "recipientOrganization.0.charityNumber"          as recipient_charity_number,
    "recipientOrganization.0.companyNumber"          as recipient_company_number,
    "fundingOrganization.0.id"                       as funder_org_id,
    "fundingOrganization.0.name"                     as funder_name,
    "grantProgramme.0.title"                         as programme_title,
    "_extracted_at",
    "_source"
from source
