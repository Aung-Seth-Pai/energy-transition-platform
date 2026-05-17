-- stg_ember__power_sector_emission
-- --------------------------------
-- Source: bronze/ember/power_sector_emission/*/*/data.json
-- Grain: one row per (entity, series, month)
--
-- Wide table — series dimension (Coal, Gas, Oil, Wind, Solar, etc.)
-- emissions_mtco2 is total CO2-equivalent emissions from each generation source.
-- share_of_emissions_pct is relative to that entity's total power sector emissions.
-- share_of_emissions_pct sums to ~100% per (entity, month) across non-aggregate series.

with

raw as (
    select
        unnest(data) as record,
        extracted_at,
        logical_date
    from read_json(
        '{{ env_var("BRONZE_DIR", "/opt/data/bronze") }}/ember/power_sector_emission/*/*/data.json',
        format        = 'auto',
        union_by_name = true,
        filename      = false
    )
),

unnested as (
    select
        record.entity                   as entity,
        record.entity_code              as entity_code,
        record.is_aggregate_entity      as is_aggregate_entity,
        record.is_aggregate_series      as is_aggregate_series,
        record.series                   as series,
        cast(record.date as date)       as month_date,
        record.emissions_mtco2          as emissions_mtco2,
        record.share_of_emissions_pct   as share_of_emissions_pct,
        cast(extracted_at as timestamp) as extracted_at,
        cast(logical_date as date)      as logical_date
    from raw
),

deduped as (
    select *
    from (
        select
            *,
            row_number() over (
                partition by entity_code, series, month_date
                order by extracted_at desc
            ) as rn
        from unnested
        where entity_code is not null
    )
    where rn = 1
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['entity_code', 'series', 'month_date']) }}
                                        as power_sector_emission_id,
        entity,
        entity_code,
        series,
        month_date,
        emissions_mtco2,
        share_of_emissions_pct,
        is_aggregate_entity,
        is_aggregate_series,
        extracted_at,
        logical_date
    from deduped
    where is_aggregate_entity = false
      and is_aggregate_series = false
)

select * from final