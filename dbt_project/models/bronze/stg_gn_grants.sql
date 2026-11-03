with source as (
    select * from {{ source('bronze', 'gn_grants') }}
)

select
    id as grant_id,
    title as grant_title,
    description as grant_description,
    currency,
    cast(amountawarded as double) as amount_awarded,
    cast(awarddate as varchar) as award_date,
    recipientorganization_id as recipient_org_id,
    recipientorganization_name as recipient_org_name,
    recipientorganization_charitynumber as recipient_charity_number,
    recipientorganization_companynumber as recipient_company_number,
    fundingorganization_id as funder_org_id,
    fundingorganization_name as funder_name,
    grantprogramme_title as programme_title,
    _extracted_at,
    _source
from source
