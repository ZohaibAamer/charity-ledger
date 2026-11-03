-- Health score must be between 0 and 100
select
    charity_number,
    health_score
from {{ ref('charity_health_scorecard') }}
where health_score < 0 or health_score > 100
