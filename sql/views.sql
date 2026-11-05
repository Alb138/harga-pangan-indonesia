-- Analysis-ready views: fact joined to its dimensions, outliers removed.

CREATE OR REPLACE VIEW v_price AS
SELECT
    f.date_key,
    f.province_id,
    p.province_name,
    p.tz_region,
    p.island_group,
    p.is_national,
    f.commodity_id,
    c.commodity_name,
    c.category_name,
    f.market_type_id,
    m.name AS market_type,
    m.chain_order,
    f.price_idr
FROM fact_price_daily AS f
JOIN dim_province    AS p USING (province_id)
JOIN dim_commodity   AS c USING (commodity_id)
JOIN dim_market_type AS m USING (market_type_id)
WHERE NOT f.is_outlier;

CREATE OR REPLACE VIEW v_price_province AS
SELECT * FROM v_price WHERE NOT is_national;

-- National series without holiday days on which only a handful of provinces reported.
CREATE OR REPLACE VIEW v_price_national AS
SELECT v.*
FROM v_price AS v
JOIN dim_date AS d USING (date_key)
WHERE v.is_national AND NOT d.is_thin_day;
