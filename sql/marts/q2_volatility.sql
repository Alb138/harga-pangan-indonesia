-- Q2. Which commodities are the least stable, and when were the biggest price shocks?
-- Series: weekly average of the national traditional-market price.

CREATE OR REPLACE TABLE mart_q2_weekly AS
WITH weekly AS (
    SELECT commodity_id, date_trunc('week', date_key) AS week, AVG(price_idr) AS price_idr
    FROM v_price_national
    WHERE market_type_id = 1
    GROUP BY ALL
)
SELECT
    commodity_id,
    CAST(week AS DATE) AS week,
    price_idr,
    price_idr / LAG(price_idr, 1) OVER w - 1 AS pct_1w,
    price_idr / LAG(price_idr, 4) OVER w - 1 AS pct_4w
FROM weekly
WINDOW w AS (PARTITION BY commodity_id ORDER BY week)
ORDER BY ALL;


-- Volatility = standard deviation of week-on-week changes within a year.
CREATE OR REPLACE TABLE mart_q2_volatility AS
SELECT
    commodity_id,
    CAST(year(week) AS INTEGER) AS year,
    stddev_samp(pct_1w) AS std_pct_1w
FROM mart_q2_weekly
WHERE pct_1w IS NOT NULL
GROUP BY ALL
ORDER BY ALL;


-- Biggest 4-week jumps per commodity. Keeping only the strongest week of each month stops
-- one long surge from filling every slot with neighbouring weeks.
CREATE OR REPLACE TABLE mart_q2_top_shocks AS
WITH best_week_per_month AS (
    SELECT commodity_id, week, pct_4w
    FROM mart_q2_weekly
    WHERE pct_4w IS NOT NULL
    QUALIFY row_number() OVER (
        PARTITION BY commodity_id, date_trunc('month', week) ORDER BY pct_4w DESC
    ) = 1
)
SELECT
    commodity_id,
    week,
    pct_4w,
    row_number() OVER (PARTITION BY commodity_id ORDER BY pct_4w DESC) AS rank
FROM best_week_per_month
QUALIFY rank <= 5
ORDER BY commodity_id, rank;
