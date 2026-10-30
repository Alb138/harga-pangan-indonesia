-- Q4 price increase between consecutive supply-chain levels.
SELECT c.commodity_name, c.category_name, q.month, q.from_order, q.from_level, q.to_level,
       ROUND(q.markup_pct, 4) AS markup_pct
FROM mart_q4_markup AS q
JOIN dim_commodity AS c USING (commodity_id)
ORDER BY c.commodity_name, q.month, q.from_order
