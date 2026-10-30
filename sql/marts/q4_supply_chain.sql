-- Q4. How much does the price grow from producer to retail?
-- Chain: Produsen -> Pedagang Besar -> Pasar Tradisional -> Pasar Modern (national series).
-- Pasar Modern is an alternative retail channel rather than a later stage, so the last step
-- reads as the price gap between the two retail channels.

CREATE OR REPLACE TABLE mart_q4_markup AS
WITH monthly AS (
    SELECT
        commodity_id,
        CAST(date_trunc('month', date_key) AS DATE) AS month,
        chain_order,
        market_type,
        AVG(price_idr) AS avg_price
    FROM v_price_national
    GROUP BY ALL
)
SELECT
    up.commodity_id,
    up.month,
    up.chain_order AS from_order,
    up.market_type AS from_level,
    down.market_type AS to_level,
    down.avg_price / up.avg_price - 1 AS markup_pct
FROM monthly AS up
JOIN monthly AS down
  ON  down.commodity_id = up.commodity_id
  AND down.month        = up.month
  AND down.chain_order  = up.chain_order + 1
ORDER BY up.commodity_id, up.month, from_order;
