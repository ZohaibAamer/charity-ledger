-- Entity resolution confidence must be between 0 and 1
select
    entity_id,
    company_match_confidence
from {{ ref('entity_resolution') }}
where company_match_confidence is not null
  and (company_match_confidence < 0 or company_match_confidence > 1)
