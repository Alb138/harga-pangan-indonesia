-- Move staged prices into the fact table, flagging values far from their local median.
-- Reference = median price of the same (province, commodity, market type) within
-- +/- $window_days calendar days. A price more than $ratio times above or below it is
-- almost always a typo in the source (e.g. 1,615 typed for 16,150).
-- A rolling window (not a calendar month) matters: in the 2021 PIHPS data one typo was
-- repeated for four weeks, enough to become the median of its month.
INSERT INTO fact_price_daily
WITH with_reference AS (
    SELECT
        *,
        median(price_idr) OVER (
            PARTITION BY province_id, commodity_id, market_type_id
            ORDER BY date_key
            RANGE BETWEEN INTERVAL ($window_days) DAYS PRECEDING
                      AND INTERVAL ($window_days) DAYS FOLLOWING
        ) AS reference_price
    FROM stg_price
)
SELECT
    CAST(date_key AS DATE),
    province_id,
    commodity_id,
    market_type_id,
    price_idr,
    price_idr > $ratio * reference_price OR price_idr < reference_price / $ratio
FROM with_reference;
