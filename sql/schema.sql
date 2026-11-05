-- Star schema for daily food prices.
-- Grain of the fact table: one price per (day, province, commodity, market type).

CREATE TABLE dim_date (
    date_key        DATE PRIMARY KEY,
    year            SMALLINT NOT NULL,
    month           TINYINT  NOT NULL,
    iso_week        TINYINT  NOT NULL,
    dow             TINYINT  NOT NULL,   -- ISO day of week: 1 = Monday ... 7 = Sunday
    idul_fitri      DATE,                -- nearest Idul Fitri, only inside the Lebaran window
    lebaran_year    SMALLINT,
    days_to_lebaran INTEGER,             -- negative = before Lebaran (H-7 = -7)
    is_ramadan      BOOLEAN NOT NULL,
    reporting_provinces INTEGER,         -- provinces with a traditional-market price that day
    is_thin_day     BOOLEAN NOT NULL DEFAULT FALSE  -- too few provinces for a national figure
);

CREATE TABLE dim_province (
    province_id   INTEGER PRIMARY KEY,   -- PIHPS id; 0 = national series
    province_name VARCHAR NOT NULL,
    bps_code      INTEGER,
    island_group  VARCHAR,
    tz_region     VARCHAR,               -- Barat (WIB), Tengah (WITA), Timur (WIT)
    capital       VARCHAR,
    lat           DOUBLE,
    lon           DOUBLE,
    is_national   BOOLEAN NOT NULL
);

CREATE TABLE dim_commodity (
    commodity_id   VARCHAR PRIMARY KEY,  -- com_1 ... com_21
    commodity_name VARCHAR NOT NULL,
    category_id    VARCHAR NOT NULL,     -- cat_1 ... cat_10
    category_name  VARCHAR NOT NULL,
    unit           VARCHAR NOT NULL
);

CREATE TABLE dim_market_type (
    market_type_id TINYINT PRIMARY KEY,  -- PIHPS price_type_id
    name           VARCHAR NOT NULL,
    chain_order    TINYINT NOT NULL      -- position in the supply chain, producer first
);

INSERT INTO dim_market_type VALUES
    (1, 'Pasar Tradisional', 3),
    (2, 'Pasar Modern',      4),
    (3, 'Pedagang Besar',    2),
    (4, 'Produsen',          1);

CREATE TABLE fact_price_daily (
    date_key       DATE    NOT NULL,
    province_id    INTEGER NOT NULL,
    commodity_id   VARCHAR NOT NULL,
    market_type_id TINYINT NOT NULL,
    price_idr      BIGINT  NOT NULL,     -- rupiah per unit (dim_commodity.unit)
    is_outlier     BOOLEAN NOT NULL,
    PRIMARY KEY (date_key, province_id, commodity_id, market_type_id)
);

CREATE TABLE ref_ump (
    bps_code INTEGER  NOT NULL,
    year     SMALLINT NOT NULL,
    ump_idr  BIGINT   NOT NULL,
    PRIMARY KEY (bps_code, year)
);

CREATE TABLE ref_basket (
    commodity_id            VARCHAR PRIMARY KEY,
    qty_kg_per_capita_week  DOUBLE NOT NULL
);
