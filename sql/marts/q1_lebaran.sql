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


-- Summary per commodity.
--   median_peak_pct : median over years of each season's highest index (size of the rise)
--   *_week          : timing read from ONE "typical season" curve - the median across years
--                     of each week's average index - so peak, start and recovery always
--                     tell a consistent story. Week -1 = H-7..H-1, week 0 = H..H+6.
CREATE OR REPLACE TABLE mart_q1_summary AS
WITH season AS (
    SELECT *, CAST(floor(t / 7) AS INTEGER) AS week
    FROM mart_q1_lebaran_index
    WHERE t >= -42   -- whole weeks after the baseline window
),
yearly_peak AS (
    SELECT commodity_id, lebaran_year, MAX(price_index) - 1 AS peak_pct
    FROM season
    GROUP BY ALL
),
typical AS (
    SELECT commodity_id, week, median(week_index) AS price_index
    FROM (
        SELECT commodity_id, lebaran_year, week, AVG(price_index) AS week_index
        FROM season
        GROUP BY ALL
    )
    GROUP BY ALL
),
timing AS (
    SELECT
        commodity_id,
        arg_max(week, price_index) AS peak_week,
        MIN(week) FILTER (WHERE price_index >= 1.05) AS start_rise_week
    FROM typical
    GROUP BY ALL
),
recovery AS (
    -- First week after the peak when the typical index is back within +5% of baseline.
    SELECT t.commodity_id, MIN(c.week) AS recover_week
    FROM timing AS t
    JOIN typical AS c
      ON c.commodity_id = t.commodity_id
     AND c.week > t.peak_week
     AND c.price_index < 1.05
    GROUP BY ALL
)
SELECT
    y.commodity_id,
    median(y.peak_pct)  AS median_peak_pct,
    ANY_VALUE(t.peak_week)       AS peak_week,
    ANY_VALUE(t.start_rise_week) AS start_rise_week,
    ANY_VALUE(r.recover_week)    AS recover_week,
    COUNT(*)            AS n_years
FROM yearly_peak AS y
JOIN timing AS t USING (commodity_id)
LEFT JOIN recovery AS r USING (commodity_id)
GROUP BY y.commodity_id
ORDER BY median_peak_pct DESC;
