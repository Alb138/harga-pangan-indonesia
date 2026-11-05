# Data Sources

All sources accessed on **2026-10-31** unless noted otherwise.

## 1. PIHPS Nasional — Bank Indonesia (food prices)

- Portal: <https://www.bi.go.id/hargapangan>
- Data is fetched from the JSON endpoints that power the portal's own price table
  (`/hargapangan/WebSite/TabelHarga/*`). There is no official API and no documented bulk
  download, so the extractor is deliberately polite: one request at a time, a 2-second pause
  between requests, a descriptive User-Agent, and a local cache so every request is made once.
- `robots.txt` (<https://www.bi.go.id/robots.txt>) allows `/` and only disallows SharePoint
  paths (`/_layouts`, `/Lists`, ...); `/hargapangan` is allowed.

### Verified facts (2026-10-31)

| Check | Result |
|---|---|
| Market types (`GetRefPriceType`) | 1 Pasar Tradisional, 2 Pasar Modern, 3 Pedagang Besar, 4 Produsen |
| Provinces (`GetRefProvince`) | **34** provinces (pre-2022 boundaries; no Papua Selatan/Tengah/Pegunungan/Barat Daya) |
| Commodities (`GetRefCommodityAndCategory`) | 10 categories (`cat_1..cat_10`), 21 commodities (`com_1..com_21`), unit `kg` for all |
| National series (`province_id=""`) | Returns data for all 4 market types |
| Earliest data | 2017-07-10 (DKI Jakarta, Pasar Tradisional) → analysis starts 2018-01-01 |
| Response shape | Wide: one row per category (`level` 1) or commodity (`level` 2), one key per business day `dd/mm/yyyy`, prices as strings like `"16,150"`, missing as `"-"` |
| Speed | One year × one province × all categories ≈ 177 KB, 20–40 s |

Observed quirk: commodity names can carry trailing spaces (`"Cabai Merah Keriting "`).

## 2. Idul Fitri dates (`data/reference/holidays.csv`)

Government (Kemenag sidang isbat / SKB) dates. Where Muhammadiyah differed (2023: 21 Apr,
2026: 20 Mar), the government date is used.

- 2026: 1 Syawal 1447 H = Saturday 21 March 2026 (sidang isbat 19 March 2026) —
  [Investortrust](https://investortrust.id/national/97702/indonesia-mandates-30-day-ramadan-as-idulfitri-lands-on-saturday),
  [Fimela](https://www.fimela.com/info/read/6301432/kapan-lebaran-2026-ini-dia-hasil-sidang-isbat-idul-fitri-jatuh-pada-sabtu-21-maret)

## 3. Provinces (`data/reference/provinces.csv`)

- `pihps_id` and `province_name` match `GetRefProvince` exactly (checked programmatically).
- `bps_code`: BPS 2-digit province codes (pre-2022 boundaries, matching PIHPS).
- `tz_region`: WIB = Barat, WITA = Tengah, WIT = Timur.
- `capital`, `lat`, `lon`: provincial capital, approximate coordinates for Tableau symbol maps
  (Kalimantan Selatan uses Banjarbaru, capital since 2022).

## 4. BPS — Badan Pusat Statistik

| Data | BPS table | Status |
|---|---|---|
| UMP 2021–2026 | Dynamic table var **2824** "Upah Minimum Provinsi (UMP) per Bulan Menurut Provinsi di Indonesia" ([link](https://jateng.bps.go.id/id/statistics-table/2/MjgyNCMy/upah-minimum-provinsi--ump--per-bulan-menurut-provinsi-di-indonesia.html)). BPS notes Papua Barat includes Papua Barat Daya and Papua includes the three new Papua provinces — matches PIHPS's 34-province basis. | Needs BPS WebAPI key |
| UMP 2018–2020 | Dynamic table var **220** "Upah Minimum Regional/Propinsi" ([link](https://www.bps.go.id/id/statistics-table/2/MjIwIzI=/upah-minimum-regional-propinsi.html)) | Needs BPS WebAPI key |
| Food basket quantities | Static table **950** "Rata-Rata Konsumsi per Kapita Seminggu Beberapa Macam Bahan Makanan Penting, 2007-2025" (Susenas) | Needs BPS WebAPI key |

The BPS website only renders the latest year of a dynamic table server-side (other years are
loaded through internal server actions), and the static table failed to render server-side, so
these tables are pulled through the official [BPS WebAPI](https://webapi.bps.go.id/) (free key).

## 5. Data quality (full build, 2026-11-05)

Command: `uv run pangan build && uv run pangan quality`

| Check | Result |
|---|---|
| Cache files | 342 (34 provinces × 9 years traditional market + 4 market types × 9 years national) |
| Price rows (`fact_price_daily`) | **1,713,633** — 2018-01-01 to 2026-09-30, 34 provinces + national, 21 commodities |
| Rows by market type | Pasar Tradisional 1,572,015 · Pasar Modern 47,827 · Pedagang Besar 47,838 · Produsen 45,953 (national producer series starts 2018-03-26) |
| Duplicate keys / null prices | 0 / 0 |
| Business-day coverage per province-year | min 92.0%, median 95.4% (missing days are public holidays) — no province-year below 80% |
| Outliers flagged (excluded from analysis) | **33** — 22 of them one typo: national producer price of *Daging Sapi Kualitas 2* recorded as ~Rp583,000 instead of ~Rp108,000 on 22 business days (2021-09-20 → 2021-10-19); the rest are single-day typos, mostly Papua Barat 2019–2021 |
| Thin days (excluded from national series) | 77 weekdays where fewer than half of the provinces reported (holiday periods such as Lebaran 2022, when only 1–2 provinces reported and the "national" price jumped 20–50% for a day) |

Two cleaning rules were changed after inspecting the real data (see `git log`):

1. Outliers are judged against a **±60-day rolling median**, not the calendar-month median —
   the beef typo above lasted long enough to *become* October 2021's median.
2. **Thin days** are removed from the national series; province series keep them.
