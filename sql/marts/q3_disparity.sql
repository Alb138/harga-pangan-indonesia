-- Q3. How far apart are prices across provinces, and is the gap narrowing?
-- Series: monthly average traditional-market price per province.

CREATE OR REPLACE TABLE mart_q3_province_index AS
WITH monthly AS (
    SELECT
        province_id,
        commodity_id,
        CAST(date_trunc('month', date_key) AS DATE) AS month,
        AVG(price_idr) AS avg_price
    FROM v_price_province
    WHERE market_type_id = 1
    GROUP BY ALL
)
SELECT
    province_id,
    commodity_id,
    month,
    avg_price,
    -- 1.25 = 25% above the typical (median) province that month
    avg_price / median(avg_price) OVER (PARTITION BY commodity_id, month) AS index_vs_median
FROM monthly
ORDER BY ALL;


-- Coefficient of variation across provinces: a single, unit-free measure of disparity.
CREATE OR REPLACE TABLE mart_q3_disparity AS
SELECT
    commodity_id,
    month,
    stddev_samp(avg_price) / AVG(avg_price) AS cv,
    COUNT(*) AS n_provinces
FROM mart_q3_province_index
GROUP BY ALL
ORDER BY ALL;
