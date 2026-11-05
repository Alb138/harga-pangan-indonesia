-- Q1 per-commodity summary across Lebaran seasons (timing in weeks relative to Lebaran).
SELECT c.commodity_name, c.category_name,
       ROUND(q.median_peak_pct, 4) AS median_peak_pct,
       q.peak_week, q.start_rise_week, q.recover_week, q.n_years
FROM mart_q1_summary AS q
JOIN dim_commodity AS c USING (commodity_id)
ORDER BY q.median_peak_pct DESC
