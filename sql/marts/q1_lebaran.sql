-- Q1. How much do prices rise around Lebaran, when does the rise start, and when does it fade?
-- Series: national traditional-market price, t = days relative to Idul Fitri (H-7 = -7).
-- Index: price / average price over the baseline weeks H-60 .. H-46 of the same year.

CREATE OR REPLACE TABLE mart_q1_lebaran_index AS
WITH national AS (
    SELECT p.commodity_id, d.lebaran_year, d.days_to_lebaran AS t, p.price_idr
    FROM v_price_national AS p
    JOIN dim_date AS d USING (date_key)
    WHERE p.market_type_id = 1
      AND d.days_to_lebaran BETWEEN -60 AND 30
),
baseline AS (
    SELECT commodity_id, lebaran_year, AVG(price_idr) AS base_price
    FROM national
    WHERE t BETWEEN -60 AND -46
    GROUP BY ALL
)
SELECT
    n.commodity_id,
    n.lebaran_year,
    n.t,
    n.price_idr,
    n.price_idr / b.base_price AS price_index
FROM national AS n
JOIN baseline AS b USING (commodity_id, lebaran_year)
ORDER BY ALL;


CREATE OR REPLACE TABLE mart_q1_summary AS
WITH after_baseline AS (
    SELECT * FROM mart_q1_lebaran_index WHERE t >= -45
),
per_year AS (
    -- Peak of each Lebaran season and the first day the index crossed +5%.
    SELECT
        commodity_id,
        lebaran_year,
        MAX(price_index) - 1 AS peak_pct,
        arg_max(t, price_index) AS peak_t,
        MIN(t) FILTER (WHERE price_index >= 1.05) AS start_rise_t
    FROM after_baseline
    GROUP BY ALL
),
recovery AS (
    -- First day after the peak when the index is back within +5% of baseline.
    SELECT y.commodity_id, y.lebaran_year, MIN(a.t) AS recover_t
    FROM per_year AS y
    JOIN after_baseline AS a
      ON a.commodity_id = y.commodity_id
     AND a.lebaran_year = y.lebaran_year
     AND a.t > y.peak_t
     AND a.price_index < 1.05
    GROUP BY ALL
)
SELECT
    y.commodity_id,
    median(y.peak_pct)     AS median_peak_pct,
    median(y.peak_t)       AS median_peak_t,
    median(y.start_rise_t) AS median_start_rise_t,
    median(r.recover_t)    AS median_recover_t,
    COUNT(*)               AS n_years
FROM per_year AS y
LEFT JOIN recovery AS r USING (commodity_id, lebaran_year)
GROUP BY y.commodity_id
ORDER BY median_peak_pct DESC;
