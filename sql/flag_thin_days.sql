-- Count, per day, the provinces that reported a traditional-market price.
-- On public holidays (e.g. around Lebaran 2022) only one or two of 34 provinces report,
-- so that day's "national" price is really one or two provinces' prices. Days below
-- $min_share of all provinces are flagged and left out of the national series.
UPDATE dim_date
SET reporting_provinces = r.n_reporting,
    is_thin_day = r.n_reporting < $min_share * r.n_provinces
FROM (
    SELECT
        d.date_key,
        COUNT(DISTINCT f.province_id) AS n_reporting,
        (SELECT COUNT(*) FROM dim_province WHERE NOT is_national) AS n_provinces
    FROM dim_date AS d
    LEFT JOIN fact_price_daily AS f
      ON  f.date_key = d.date_key
      AND f.market_type_id = 1
      AND f.province_id <> 0
    GROUP BY d.date_key
) AS r
WHERE dim_date.date_key = r.date_key;
