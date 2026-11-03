{% macro check_source_freshness(source_name, table_name, max_age_hours) %}

{% set query %}
    select
        max(_extracted_at) as last_extracted,
        current_timestamp as checked_at,
        case
            when max(_extracted_at) < current_timestamp - interval '{{ max_age_hours }} hours'
                then 'STALE'
            else 'FRESH'
        end as status
    from {{ source(source_name, table_name) }}
{% endset %}

{% if execute %}
    {% set result = run_query(query) %}
    {% set status = result.columns[2].values()[0] %}
    {{ log(table_name ~ ": " ~ status ~ " (last: " ~ result.columns[0].values()[0] ~ ")", info=true) }}
    {% if status == 'STALE' %}
        {{ exceptions.warn("Source " ~ table_name ~ " is stale (>" ~ max_age_hours ~ "h)") }}
    {% endif %}
{% endif %}

{% endmacro %}
