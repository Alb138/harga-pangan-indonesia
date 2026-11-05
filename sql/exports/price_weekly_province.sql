-- Weekly traditional-market price per province, for the explorer view.
SELECT province_name, tz_region, commodity_name, category_name,
       CAST(date_trunc('week', date_key) AS DATE) AS week,
       CAST(ROUND(AVG(price_idr)) AS BIGINT) AS avg_price_idr
FROM v_price_province
WHERE market_type_id = 1
GROUP BY ALL
ORDER BY province_name, commodity_name, week
