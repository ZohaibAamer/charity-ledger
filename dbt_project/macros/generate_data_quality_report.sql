{% macro generate_data_quality_report() %}

{% set report_query %}
    with bronze_stats as (
        select
            'cc_charities' as table_name,
            count(*) as row_count,
            max(_extracted_at) as last_extracted
        from {{ source('bronze', 'cc_charities') }}
        union all
        select
            'cc_finances',
            count(*),
            max(_extracted_at)
        from {{ source('bronze', 'cc_finances') }}
        union all
        select
            'cc_trustees',
            count(*),
            max(_extracted_at)
        from {{ source('bronze', 'cc_trustees') }}
        union all
        select
            'ch_companies',
            count(*),
            max(_extracted_at)
        from {{ source('bronze', 'ch_companies') }}
        union all
        select
            'gn_grants',
            count(*),
            max(_extracted_at)
        from {{ source('bronze', 'gn_grants') }}
    ),

    silver_stats as (
        select
            'entity_resolution' as table_name,
            count(*) as row_count,
            count(distinct charity_number) as unique_charities,
            count(company_number) as matched_companies,
            avg(company_match_confidence) as avg_confidence
        from {{ ref('entity_resolution') }}
    ),

    gold_stats as (
        select
            count(*) as total_charities,
            avg(health_score) as avg_health_score,
            min(health_score) as min_health_score,
            max(health_score) as max_health_score,
            count(case when health_score >= 75 then 1 end) as healthy_count,
            count(case when health_score >= 50 and health_score < 75 then 1 end) as moderate_count,
            count(case when health_score < 50 then 1 end) as at_risk_count
        from {{ ref('charity_health_scorecard') }}
    )

    select
        current_timestamp as report_generated_at,
        (select json_group_array(json_object(
            'table', table_name,
            'rows', row_count,
            'last_extracted', last_extracted
        )) from bronze_stats) as bronze_summary,
        (select json_object(
            'entities', row_count,
            'unique_charities', unique_charities,
            'matched_companies', matched_companies,
            'avg_confidence', round(avg_confidence, 3)
        ) from silver_stats) as silver_summary,
        (select json_object(
            'total_charities', total_charities,
            'avg_health_score', round(avg_health_score, 1),
            'min_score', min_health_score,
            'max_score', max_health_score,
            'healthy', healthy_count,
            'moderate', moderate_count,
            'at_risk', at_risk_count
        ) from gold_stats) as gold_summary
{% endset %}

{% if execute %}
    {% set results = run_query(report_query) %}
    {{ log("=" * 60, info=true) }}
    {{ log("DATA QUALITY REPORT", info=true) }}
    {{ log("=" * 60, info=true) }}
    {{ log("Generated: " ~ results.columns[0].values()[0], info=true) }}
    {{ log("Bronze: " ~ results.columns[1].values()[0], info=true) }}
    {{ log("Silver: " ~ results.columns[2].values()[0], info=true) }}
    {{ log("Gold: " ~ results.columns[3].values()[0], info=true) }}
    {{ log("=" * 60, info=true) }}
{% endif %}

{% endmacro %}
