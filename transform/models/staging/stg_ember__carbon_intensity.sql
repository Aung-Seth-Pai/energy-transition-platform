-- stg_ember__carbon_intensity
-- ---------------------------
-- Source: bronze/ember/carbon_intensity/*/*/data.json
-- Grain: one row per (entity, month)
--
-- Narrow table — no series dimension.
-- emissions_intensity_gco2_per_kwh is the weighted average carbon intensity
-- of the entire grid, accounting for all generation sources including imports.
--
-- Range in sample data: 0.0 (fully renewable grids) to 895.24 (coal-heavy grids).
-- Zero values are real (e.g. Iceland — near 100% geothermal/hydro).

with

raw as (
    select
        unnest(data) as record,
        extracted_at,
        logical_date
    from read_json(
        '{{ env_var("BRONZE_DIR", "/opt/data/bronze") }}/ember/carbon_intensity/*/*/data.json',
        format        = 'auto',
        union_by_name = true,
        filename      = false
    )
),

unnested as (
    select
        record.entity                            as entity,
        record.entity_code                       as entity_code,
        record.is_aggregate_entity               as is_aggregate_entity,
        cast(record.date as date)                as month_date,
        record.emissions_intensity_gco2_per_kwh  as emissions_intensity_gco2_per_kwh,
        cast(extracted_at as timestamp)          as extracted_at,
        cast(logical_date as date)               as logical_date
    from raw
),

deduped as (
    select *
    from (
        select
            *,
            row_number() over (
                partition by entity_code, month_date
                order by extracted_at desc
            ) as rn
        from unnested
        where entity_code is not null
    )
    where rn = 1
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['entity_code', 'month_date']) }}
                                                as carbon_intensity_id,
        entity,
        entity_code,
        month_date,
        emissions_intensity_gco2_per_kwh,
        is_aggregate_entity,
        extracted_at,
        logical_date
    from deduped
    where is_aggregate_entity = false
)

select * from final