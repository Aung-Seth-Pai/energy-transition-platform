-- stg_ember__generation
-- ---------------------
-- Source: bronze/ember/generation/*/*/data.json
-- Grain: one row per (entity, series, month)
--
-- Key decisions:
-- - Filters out aggregate entities (e.g. "World", "EU") and aggregate series
--   (e.g. "Total", "Renewables") to prevent double-counting in downstream models.
--   Aggregates are preserved in a separate boolean flag for optional use.
-- - date cast to DATE from the ISO string '2025-12-01' that Ember returns.
-- - Negative generation_twh values are real (pumped hydro net storage) -- kept as-is.
-- - Deduplicates by keeping the latest extracted_at per grain in case of re-runs
--   within the same logical_date window.

with

raw as (
    select
        unnest(data) as record,
        extracted_at,
        logical_date
    from read_json(
        '{{ env_var("BRONZE_DIR", "/opt/data/bronze") }}/ember/generation/*/*/data.json',
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
        record.generation_twh           as generation_twh,
        record.share_of_generation_pct  as share_of_generation_pct,
        cast(extracted_at as timestamp) as extracted_at,
        cast(logical_date as date)      as logical_date
    from raw
),

-- Deduplicate: if the same grain appears in multiple extractions
-- (due to 6-month rolling lookback re-runs), keep the freshest one.
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
        -- Only deduplicate non-aggregates; aggregates are filtered next anyway
        where entity_code is not null
    )
    where rn = 1
),

final as (
    select
        -- Surrogate key
        {{ dbt_utils.generate_surrogate_key(['entity_code', 'series', 'month_date']) }}
                                        as generation_id,
        entity,
        entity_code,
        series,
        month_date,

        -- Metrics
        generation_twh,
        share_of_generation_pct,

        -- Filter flags (kept for transparency, filtered below)
        is_aggregate_entity,
        is_aggregate_series,

        -- Audit columns
        extracted_at,
        logical_date
    from deduped
    -- Exclude aggregate rows — downstream marts sum from atomic rows only.
    -- Re-include by removing this filter if you need regional aggregates.
    where is_aggregate_entity = false
      and is_aggregate_series = false
)

select * from final