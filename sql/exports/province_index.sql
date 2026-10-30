-- Q3 monthly province price vs. the median province.
SELECT p.province_name, p.tz_region, p.island_group, p.lat, p.lon,
       c.commodity_name, c.category_name, q.month, ROUND(q.avg_price) AS avg_price,
       ROUND(q.index_vs_median, 4) AS index_vs_median
FROM mart_q3_province_index AS q
JOIN dim_province AS p USING (province_id)
JOIN dim_commodity AS c USING (commodity_id)
ORDER BY c.commodity_name, q.month, p.province_name
