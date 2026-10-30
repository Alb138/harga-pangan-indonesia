-- Q2 five biggest 4-week jumps per commodity.
SELECT c.commodity_name, c.category_name, q.week, ROUND(q.pct_4w, 4) AS pct_4w, q.rank
FROM mart_q2_top_shocks AS q
JOIN dim_commodity AS c USING (commodity_id)
ORDER BY c.commodity_name, q.rank
