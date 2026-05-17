-- stg_ember__installed_capacity
-- -----------------------------
-- Source: bronze/ember/installed_capacity/*/*/data.json
-- Grain: one row per (entity, series, month)
--
-- Wide table — series dimension (Onshore wind, Solar, Coal, etc.)
-- capacity_gw is nameplate installed capacity — NOT the same as generation.
-- capacity_w_per_capita normalises by population — useful for cross-country comparison.
-- capacity_w_per_capita can be null for aggregate entities (no single population).

with

raw as (
    select
        unnest(data) as record,
        extracted_at,
        logical_date
    from read_json(
        '{{ env_var("BRONZE_DIR", "/opt/data/bronze") }}/ember/installed_capacity/*/*/data.json',
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
        record.capacity_gw              as capacity_gw,
        record.capacity_w_per_capita    as capacity_w_per_capita,
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
                                        as installed_capacity_id,
        entity,
        entity_code,
        series,
        month_date,
        capacity_gw,
        capacity_w_per_capita,
        is_aggregate_entity,
        is_aggregate_series,
        extracted_at,
        logical_date
    from deduped
    where is_aggregate_entity = false
      and is_aggregate_series = false
)

select * from final