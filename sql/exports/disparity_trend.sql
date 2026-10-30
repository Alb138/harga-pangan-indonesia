-- Q3 disparity across provinces (coefficient of variation) per month.
SELECT c.commodity_name, c.category_name, q.month, ROUND(q.cv, 4) AS cv, q.n_provinces
FROM mart_q3_disparity AS q
JOIN dim_commodity AS c USING (commodity_id)
ORDER BY c.commodity_name, q.month
