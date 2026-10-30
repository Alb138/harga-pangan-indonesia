-- One row per calendar day, tagged with its distance to the nearest Idul Fitri.
-- Parameters: $start, $end (DATE), $win_lo, $win_hi (Lebaran window in days).
INSERT INTO dim_date
WITH days AS (
    SELECT CAST(d AS DATE) AS date_key
    FROM range(CAST($start AS DATE), CAST($end AS DATE) + INTERVAL 1 DAY, INTERVAL 1 DAY) t(d)
),
nearest AS (
    -- For each day, the Idul Fitri closest to it (Lebarans are ~354 days apart).
    SELECT
        days.date_key,
        h.idul_fitri,
        h.year AS lebaran_year,
        date_diff('day', h.idul_fitri, days.date_key) AS offset_days,
        row_number() OVER (
            PARTITION BY days.date_key
            ORDER BY abs(date_diff('day', h.idul_fitri, days.date_key))
        ) AS rn
    FROM days
    CROSS JOIN stg_holidays AS h
),
windowed AS (
    SELECT
        date_key,
        offset_days BETWEEN $win_lo AND $win_hi AS in_window,
        idul_fitri,
        lebaran_year,
        offset_days
    FROM nearest
    WHERE rn = 1
)
SELECT
    date_key,
    year(date_key),
    month(date_key),
    weekofyear(date_key),
    isodow(date_key),
    CASE WHEN in_window THEN idul_fitri END,
    CASE WHEN in_window THEN lebaran_year END,
    CASE WHEN in_window THEN offset_days END,
    -- Ramadan approximated as the 30 days before Idul Fitri.
    in_window AND offset_days BETWEEN -30 AND -1
FROM windowed
ORDER BY date_key;
