-- Q2 yearly volatility (std. dev. of week-on-week change).
SELECT c.commodity_name, c.category_name, q.year, ROUND(q.std_pct_1w, 4) AS std_pct_1w
FROM mart_q2_volatility AS q
JOIN dim_commodity AS c USING (commodity_id)
ORDER BY c.commodity_name, q.year
