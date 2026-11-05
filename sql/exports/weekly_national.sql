-- Q2 weekly national prices with 1- and 4-week changes.
SELECT c.commodity_name, c.category_name, q.week, CAST(ROUND(q.price_idr) AS BIGINT) AS price_idr,
       ROUND(q.pct_1w, 4) AS pct_1w, ROUND(q.pct_4w, 4) AS pct_4w
FROM mart_q2_weekly AS q
JOIN dim_commodity AS c USING (commodity_id)
ORDER BY c.commodity_name, q.week
