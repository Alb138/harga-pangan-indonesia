-- Move staged prices into the fact table, flagging values far from their monthly median.
-- A price more than $ratio times above or below the median of its
-- (province, commodity, market type, month) is almost always a typo in the source,
-- e.g. 1,615 typed for 16,150.
INSERT INTO fact_price_daily
WITH monthly_median AS (
    SELECT
        province_id,
        commodity_id,
        market_type_id,
        date_trunc('month', date_key) AS month,
        median(price_idr) AS median_price
    FROM stg_price
    GROUP BY ALL
)
SELECT
    CAST(s.date_key AS DATE),
    s.province_id,
    s.commodity_id,
    s.market_type_id,
    s.price_idr,
    s.price_idr > $ratio * m.median_price OR s.price_idr < m.median_price / $ratio
FROM stg_price AS s
JOIN monthly_median AS m
  ON  m.province_id    = s.province_id
  AND m.commodity_id   = s.commodity_id
  AND m.market_type_id = s.market_type_id
  AND m.month          = date_trunc('month', s.date_key);
