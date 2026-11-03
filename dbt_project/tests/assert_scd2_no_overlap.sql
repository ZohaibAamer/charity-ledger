-- No overlapping validity periods for the same trustee
select
    a.charity_number,
    a.trustee_id,
    a.valid_from as a_from,
    a.valid_to as a_to,
    b.valid_from as b_from,
    b.valid_to as b_to
from {{ ref('scd2_trustees') }} a
inner join {{ ref('scd2_trustees') }} b
    on a.charity_number = b.charity_number
    and a.trustee_id = b.trustee_id
    and a.surrogate_key != b.surrogate_key
where a.valid_from < coalesce(b.valid_to, '9999-12-31'::timestamp)
  and b.valid_from < coalesce(a.valid_to, '9999-12-31'::timestamp)
