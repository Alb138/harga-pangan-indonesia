-- Q1 daily index around each Lebaran (national traditional market).
SELECT c.commodity_name, c.category_name, q.lebaran_year, q.t, q.price_idr,
       ROUND(q.price_index, 4) AS price_index
FROM mart_q1_lebaran_index AS q
JOIN dim_commodity AS c USING (commodity_id)
ORDER BY c.commodity_name, q.lebaran_year, q.t
