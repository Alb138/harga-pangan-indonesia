-- Q1 per-commodity summary across Lebaran seasons.
SELECT c.commodity_name, c.category_name,
       ROUND(q.median_peak_pct, 4) AS median_peak_pct, q.median_peak_t,
       q.median_start_rise_t, q.median_recover_t, q.n_years
FROM mart_q1_summary AS q
JOIN dim_commodity AS c USING (commodity_id)
ORDER BY q.median_peak_pct DESC
