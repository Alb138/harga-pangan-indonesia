-- Q5. What share of the provincial minimum wage (UMP) does a monthly food basket cost?
-- Basket: BPS Susenas per-capita weekly quantities (ref_basket) x household size,
-- priced at the province's monthly average traditional-market price.

CREATE OR REPLACE TABLE mart_q5_affordability AS
WITH monthly_price AS (
    SELECT
        p.province_id,
        CAST(date_trunc('month', p.date_key) AS DATE) AS month,
        p.commodity_id,
        AVG(p.price_idr) AS avg_price
    FROM v_price_province AS p
    JOIN ref_basket AS b USING (commodity_id)
    WHERE p.market_type_id = 1
    GROUP BY ALL
),
basket AS (
    SELECT
        m.province_id,
        m.month,
        SUM(m.avg_price * b.qty_kg_per_capita_week)
            * 52.0 / 12 * getvariable('household_size') AS basket_cost_idr,
        COUNT(*) AS n_items
    FROM monthly_price AS m
    JOIN ref_basket AS b USING (commodity_id)
    GROUP BY ALL
)
SELECT
    k.province_id,
    CAST(year(k.month) AS INTEGER) AS year,
    k.month,
    k.basket_cost_idr,
    u.ump_idr,
    k.basket_cost_idr / u.ump_idr AS share_of_ump
FROM basket AS k
JOIN dim_province AS p USING (province_id)
JOIN ref_ump AS u
  ON u.bps_code = p.bps_code AND u.year = year(k.month)
-- Only months where every basket item has a price; a partial basket would look cheap.
WHERE k.n_items = (SELECT COUNT(*) FROM ref_basket)
ORDER BY ALL;
