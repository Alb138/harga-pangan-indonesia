-- Share of business days (Mon-Fri) with at least one traditional-market price,
-- per province and year. Provinces with no data in a year show 0.
WITH business_days AS (
    SELECT year, COUNT(*) AS n_days
    FROM dim_date
    WHERE dow <= 5
    GROUP BY year
),
observed AS (
    SELECT province_id, year(date_key) AS year, COUNT(DISTINCT date_key) AS n_obs
    FROM fact_price_daily
    WHERE market_type_id = 1
    GROUP BY ALL
)
SELECT
    p.province_name,
    CAST(b.year AS INTEGER) AS year,
    COALESCE(o.n_obs, 0) / b.n_days AS pct_business_days
FROM dim_province AS p
CROSS JOIN business_days AS b
LEFT JOIN observed AS o
  ON o.province_id = p.province_id AND o.year = b.year
WHERE NOT p.is_national
ORDER BY p.province_name, b.year;
