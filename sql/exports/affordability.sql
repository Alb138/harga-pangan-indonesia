-- Q5 monthly food basket cost vs. the provincial minimum wage.
SELECT p.province_name, p.tz_region, p.island_group, p.lat, p.lon,
       q.year, q.month, CAST(ROUND(q.basket_cost_idr) AS BIGINT) AS basket_cost_idr, q.ump_idr,
       ROUND(q.share_of_ump, 4) AS share_of_ump
FROM mart_q5_affordability AS q
JOIN dim_province AS p USING (province_id)
ORDER BY p.province_name, q.month
