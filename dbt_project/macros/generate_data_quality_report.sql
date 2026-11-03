{% macro generate_data_quality_report() %}

{% set bronze_query %}
    select
        table_name,
        row_count,
        last_extracted
    from (
        select 'cc_charities' as table_name, count(*) as row_count, max(_extracted_at) as last_extracted from {{ source('bronze', 'cc_charities') }}
        union all
        select 'cc_finances', count(*), max(_extracted_at) from {{ source('bronze', 'cc_finances') }}
        union all
        select 'cc_trustees', count(*), max(_extracted_at) from {{ source('bronze', 'cc_trustees') }}
        union all
        select 'ch_companies', count(*), max(_extracted_at) from {{ source('bronze', 'ch_companies') }}
        union all
        select 'gn_grants', count(*), max(_extracted_at) from {{ source('bronze', 'gn_grants') }}
    )
{% endset %}

{% set silver_query %}
    select
        count(*) as entity_count,
        count(distinct charity_number) as unique_charities,
        count(company_number) as matched_companies,
        round(avg(company_match_confidence), 3) as avg_confidence
    from {{ ref('entity_resolution') }}
{% endset %}

{% set gold_query %}
    select
        count(*) as total_charities,
        round(avg(health_score), 1) as avg_health_score,
        min(health_score) as min_health_score,
        max(health_score) as max_health_score,
        count(case when health_score >= 75 then 1 end) as healthy_count,
        count(case when health_score >= 50 and health_score < 75 then 1 end) as moderate_count,
        count(case when health_score < 50 then 1 end) as at_risk_count
    from {{ ref('charity_health_scorecard') }}
{% endset %}

{% if execute %}
    {{ log("=" * 60, info=true) }}
    {{ log("DATA QUALITY REPORT", info=true) }}
    {{ log("=" * 60, info=true) }}

    {% set bronze_results = run_query(bronze_query) %}
    {{ log("", info=true) }}
    {{ log("BRONZE LAYER:", info=true) }}
    {% for row in bronze_results.rows() %}
        {{ log("  " ~ row[0] ~ ": " ~ row[1] ~ " rows (last: " ~ row[2] ~ ")", info=true) }}
    {% endfor %}

    {% set silver_results = run_query(silver_query) %}
    {{ log("", info=true) }}
    {{ log("SILVER LAYER:", info=true) }}
    {{ log("  Entities: " ~ silver_results.columns[0].values()[0], info=true) }}
    {{ log("  Unique charities: " ~ silver_results.columns[1].values()[0], info=true) }}
    {{ log("  Matched companies: " ~ silver_results.columns[2].values()[0], info=true) }}
    {{ log("  Avg confidence: " ~ silver_results.columns[3].values()[0], info=true) }}

    {% set gold_results = run_query(gold_query) %}
    {{ log("", info=true) }}
    {{ log("GOLD LAYER:", info=true) }}
    {{ log("  Total charities: " ~ gold_results.columns[0].values()[0], info=true) }}
    {{ log("  Avg health score: " ~ gold_results.columns[1].values()[0], info=true) }}
    {{ log("  Score range: " ~ gold_results.columns[2].values()[0] ~ " - " ~ gold_results.columns[3].values()[0], info=true) }}
    {{ log("  Healthy (>=75): " ~ gold_results.columns[4].values()[0], info=true) }}
    {{ log("  Moderate (50-74): " ~ gold_results.columns[5].values()[0], info=true) }}
    {{ log("  At risk (<50): " ~ gold_results.columns[6].values()[0], info=true) }}

    {{ log("=" * 60, info=true) }}
{% endif %}

{% endmacro %}
