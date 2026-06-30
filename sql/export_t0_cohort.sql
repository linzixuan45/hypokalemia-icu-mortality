-- export_t0_cohort.sql
-- MIMIC-III v1.4 / MIMIC-IV v2.2 template for co-author offline export
-- Output: data/mimic_t0_labs.parquet (one row per index ICU stay)
--
-- Columns: subject_id, hadm_id, stay_id, icu_intime, t0_charttime,
--          first_k_lab_charttime, potassium_at_t0, hypokalemia_stratum

-- === MIMIC-IV example (adapt schema for MIMIC-III icustays) ===
WITH first_icu AS (
    SELECT DISTINCT ON (hadm_id)
        subject_id,
        hadm_id,
        stay_id,
        intime AS icu_intime,
        outtime AS icu_outtime
    FROM mimiciv_icu.icustays
    ORDER BY hadm_id, intime
),
k_labs AS (
    SELECT
        fi.subject_id,
        fi.hadm_id,
        fi.stay_id,
        fi.icu_intime,
        le.charttime,
        le.valuenum AS potassium
    FROM first_icu fi
    JOIN mimiciv_hosp.labevents le
        ON le.subject_id = fi.subject_id
        AND le.hadm_id = fi.hadm_id
    WHERE le.itemid IN (50971, 50822)  -- potassium itemids (verify for your build)
      AND le.valuenum IS NOT NULL
),
first_k_lab AS (
    SELECT DISTINCT ON (stay_id)
        stay_id,
        charttime AS first_k_lab_charttime,
        potassium AS first_k_potassium
    FROM k_labs
    ORDER BY stay_id, charttime
),
t0 AS (
    SELECT DISTINCT ON (stay_id)
        kl.subject_id,
        kl.hadm_id,
        kl.stay_id,
        kl.icu_intime,
        kl.charttime AS t0_charttime,
        kl.potassium AS potassium_at_t0
    FROM k_labs kl
    WHERE kl.potassium < 3.5
    ORDER BY stay_id, charttime
)
SELECT
    t.subject_id,
    t.hadm_id,
    t.stay_id,
    t.icu_intime,
    t.t0_charttime,
    f.first_k_lab_charttime,
    t.potassium_at_t0,
    CASE
        WHEN t.t0_charttime <= f.first_k_lab_charttime + INTERVAL '24 hours'
             AND f.first_k_potassium < 3.5
        THEN 'admission'
        ELSE 'acquired'
    END AS hypokalemia_stratum,
    EXTRACT(EPOCH FROM (t.t0_charttime - t.icu_intime)) / 3600.0 AS hours_icu_to_t0
FROM t0 t
JOIN first_k_lab f ON f.stay_id = t.stay_id
WHERE EXTRACT(EPOCH FROM (t.icu_outtime - t.icu_intime)) / 3600.0 >= 24;
