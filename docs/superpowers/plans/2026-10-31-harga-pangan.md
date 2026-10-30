# Harga Pangan Indonesia — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (Native, dipilih) to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Projek portfolio Data Analyst end-to-end (SQL + Python + Tableau) yang menganalisis harga pangan harian Indonesia per provinsi 2018–2026 dari PIHPS Bank Indonesia + data BPS, dikemas sebagai repo GitHub siap tunjuk ke recruiter.

**Architecture:** Python mengambil data PIHPS dari endpoint JSON publik (sopan, berurutan, cache + resume) → cleaning (wide→long, parsing harga/tanggal) → DuckDB star schema → 5 mart SQL (satu per pertanyaan bisnis) → notebook Python (chart + statistik sederhana) → CSV agregat untuk dashboard Tableau Public yang dibuat user.

**Tech Stack:** Python 3.13 via `uv`, DuckDB, pandas, pyarrow, requests, numpy, scipy, matplotlib, seaborn, Jupyter, pytest, ruff; Tableau Public (manual oleh user).

**Spec:** bagian "Context" + "Desain" di bawah (disetujui user di chat 2026-10-31). Task 1 menyalin dokumen ini ke `docs/superpowers/specs/2026-10-31-harga-pangan-design.md` di repo.

---

## Context

User: mahasiswa CS semester 5, butuh portfolio untuk magang Data Analyst/Data Scientist. Keputusan yang sudah diambil bersama:
- Stack: **SQL + Python + Dashboard**; dashboard **Tableau Public** (link publik untuk CV).
- Data: **publik Indonesia, harga pangan** (dipilih karena jarang dipakai di portfolio, dibanding Olist/Telco/Titanic).
- Pembagian kerja: **Claude membangun semuanya + penjelasan lengkap**; user hanya membuat dashboard Tableau (aplikasi desktop) dengan panduan.
- Kualitas udara = **projek kedua** (di luar scope plan ini).

Hasil verifikasi sumber data (2026-10-31):
- PIHPS BI publik tanpa login. Base `https://www.bi.go.id/hargapangan/WebSite/TabelHarga/`:
  `GetRefPriceType` (1 Pasar Tradisional, 2 Pasar Modern, 3 Pedagang Besar, 4 Produsen), `GetRefProvince` (`{"id":13,"name":"DKI Jakarta"}`…), `GetRefCommodityAndCategory` (`cat_1..cat_10`, `com_1..com_21`, field `cat_id`, `denomination`).
- `GetGridDataDaerah` params: `price_type_id, comcat_id` (dipisah koma), `province_id, regency_id="", market_id="", tipe_laporan=1, start_date, end_date` (YYYY-MM-DD). Response: `{"data":[{"no":"I","name":"Beras","level":1,"01/03/2024":"16,150",...},{"no":1,"name":"Beras Kualitas Bawah I","level":2,...}]}`. Level 1 = rata-rata kategori, level 2 = komoditas. Tanggal **dd/mm/yyyy**, hanya hari kerja. Ada nama ber-spasi di akhir (`"Cabai Merah Keriting "`).
- Semua 10 kategori × 1 provinsi × 1 tahun = 1 request, ±177 KB, **±40 detik** (server lambat). Download penuh ±378 request ≈ 4–5 jam → jalankan di background, bisa resume.

## Desain (disetujui)

**Skenario (fiktif, disebut jelas di README):** analis di tim procurement jaringan katering nasional yang membeli bahan pokok di banyak provinsi.

**5 pertanyaan bisnis → mart SQL:**
1. **Efek Lebaran** (`mart_q1_*`): kenaikan puncak per komoditas, mulai H-berapa naik, kapan turun → kapan menyetok.
2. **Volatilitas & guncangan** (`mart_q2_*`): komoditas paling tidak stabil + lonjakan terbesar → kandidat kontrak harga tetap.
3. **Disparitas wilayah** (`mart_q3_*`): indeks harga provinsi vs median nasional, tren CV antar provinsi, Barat/Tengah/Timur → lokasi buffer stock.
4. **Rantai pasok** (`mart_q4_markup`): markup Produsen → Pedagang Besar → Pasar Tradisional → Pasar Modern.
5. **Keterjangkauan** (`mart_q5_affordability`): biaya paket sembako bulanan rumah tangga sebagai % UMP per provinsi.

**Data:** PIHPS Pasar Tradisional per provinsi (semua provinsi) + 4 jenis pasar level nasional, harian 2018-01-01 → 2026-09-30 (±2 juta baris); BPS: UMP per provinsi per tahun, konsumsi per kapita (Susenas) untuk keranjang; kalender Idul Fitri.

**Star schema DuckDB:** `fact_price_daily` + `dim_date`, `dim_province` (baris `province_id=0` = Nasional), `dim_commodity`, `dim_market_type`; view `v_price_province` / `v_price_national` (tanpa outlier).

**Deliverable:** repo `harga-pangan-indonesia` (README Inggris: temuan, rekomendasi, link Tableau, cara run), `docs/PENJELASAN.md` (Indonesia: tiap langkah + alasan + Q&A interview), `docs/TABLEAU_GUIDE.md`, draft bullet CV.

## Global Constraints

- Lokasi repo: `C:\Users\Albert Mario Laurent\Kuliah\Data Analyst Project\harga-pangan-indonesia\` (repo git sendiri; folder induk nanti juga menampung projek kualitas udara).
- Python 3.13 (`uv python pin 3.13`), nama paket `pangan`, layout `src/pangan/`; semua perintah via `uv run ...` (Windows).
- Periode: `START_DATE = date(2018, 1, 1)`, `END_DATE = date(2026, 9, 30)`.
- Scraping sopan: berurutan (tanpa paralel), `REQUEST_DELAY_S = 2.0` antar request, `TIMEOUT_S = 120`, `MAX_RETRIES = 3` dengan backoff `5 * 2**attempt` detik, `USER_AGENT = "Mozilla/5.0 (compatible; harga-pangan-indonesia/0.1; educational portfolio project)"`. Jangan kirim email user ke server mana pun.
- Atribusi wajib di README & dashboard: "Sumber: PIHPS Nasional, Bank Indonesia; Badan Pusat Statistik".
- Harga disimpan `INTEGER` rupiah per satuan (`dim_commodity.unit`). Harga kosong (`"-"`) tidak masuk fact.
- Git-ignore: `data/raw/`, `warehouse/`, `.venv/`, `.ipynb_checkpoints/`, `__pycache__/`. Di-commit: `data/reference/*.csv`, `exports/tableau/*.csv` (jika file > 50 MB, jangan commit; catat di README cara regenerasi), `reports/figures/*.png`, notebook beserta output.
- Semua angka di README/PENJELASAN harus berasal dari output mart yang benar-benar dijalankan — dilarang mengarang insight.
- Commit message diakhiri `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Tidak ada push/remote tanpa izin eksplisit user.
- Sebelum menulis kode chart (Task 7) dan spesifikasi dashboard (Task 8): load skill `dataviz`.

## Review Focus

1. **Tanggal day-first:** `"01/03/2024"` harus jadi 1 Maret 2024, bukan 3 Januari → test di Task 3.
2. **Provinsi/tahun tanpa data** (provinsi pemekaran Papua sebelum terbentuk, atau response `{"data": []}`) → DataFrame kosong ber-skema benar, build tidak crash, coverage 0% terlihat di quality report → test di Task 3 & Task 4.
3. **Download terputus** (timeout/koneksi server BI) → jalankan ulang melanjutkan dari cache, tidak ada file cache setengah jadi → test di Task 2.
4. **Salah input di sumber** (mis. `1,615` padahal `16,150`) → ditandai `is_outlier`, tidak ikut rata-rata → test di Task 4.
5. **Data pendukung bolong** (UMP provinsi/tahun tidak ada, atau ada item keranjang yang hilang di bulan tertentu) → baris itu dikeluarkan dari mart Q5, bukan dibagi NULL/nol atau dihitung dengan keranjang parsial → test di Task 5.

---

### Task 1: Scaffold repo, verifikasi sumber, data referensi

**Files:**
- Create: `harga-pangan-indonesia/` via `uv init --package --python 3.13 --name pangan harga-pangan-indonesia`
- Create: `.gitignore`, `src/pangan/config.py`, `docs/DATA_SOURCES.md`, `docs/superpowers/specs/2026-10-31-harga-pangan-design.md`, `docs/superpowers/plans/2026-10-31-harga-pangan.md` (salinan file ini)
- Create: `data/reference/provinces.csv`, `holidays.csv`, `ump.csv`, `basket.csv`
- Test: `tests/test_reference.py`

**Interfaces:**
- Produces: `pangan.config` konstanta `BASE_URL, START_DATE, END_DATE, REQUEST_DELAY_S, TIMEOUT_S, MAX_RETRIES, USER_AGENT, HOUSEHOLD_SIZE = 4, OUTLIER_RATIO = 3.0, LEBARAN_WINDOW = (-90, 45)`, path `ROOT, RAW_DIR = ROOT/"data/raw/pihps", REF_DIR = ROOT/"data/reference", WAREHOUSE_PATH = ROOT/"warehouse/pangan.duckdb", SQL_DIR = ROOT/"sql", EXPORT_DIR = ROOT/"exports/tableau", FIG_DIR = ROOT/"reports/figures"`.
- CSV schemas:
  - `provinces.csv`: `pihps_id,province_name,bps_code,island_group,tz_region,capital,lat,lon,valid_from_year` — `tz_region ∈ {Barat, Tengah, Timur}` (WIB/WITA/WIT), `island_group ∈ {Sumatera, Jawa, Bali-Nusa Tenggara, Kalimantan, Sulawesi, Maluku-Papua}`.
  - `holidays.csv`: `year,idul_fitri` — 2018-06-15, 2019-06-05, 2020-05-24, 2021-05-13, 2022-05-02, 2023-04-22, 2024-04-10, 2025-03-31, 2026-03-20 (verifikasi tiap tanggal ke SKB/Kemenag; koreksi jika beda).
  - `ump.csv`: `bps_code,year,ump_idr` (2018–2026, dari tabel BPS "Upah Minimum Provinsi").
  - `basket.csv`: `commodity_id,qty_kg_per_capita_week,source` — dari BPS Susenas (konsumsi per kapita seminggu) untuk beras, daging ayam ras, telur ayam ras, minyak goreng, gula pasir, bawang merah, bawang putih, cabai merah, cabai rawit; dipetakan ke satu `com_*` per item.

- [ ] **Step 1:** Scaffold `uv`, `uv add duckdb pandas pyarrow requests numpy scipy matplotlib seaborn`, `uv add --dev pytest ruff jupyter ipykernel`, `git init`, `.gitignore`, salin plan/spec ke `docs/superpowers/`.
- [ ] **Step 2: Verifikasi sumber (curl, read-only), catat di `docs/DATA_SOURCES.md`:** (a) `province_id=` kosong mengembalikan seri nasional untuk keempat `price_type_id`; (b) tanggal paling awal yang tersedia (jika < 2018, START_DATE tetap 2018; jika > 2018, ubah START_DATE dan catat); (c) daftar lengkap provinsi `GetRefProvince` (jumlah, ada/tidaknya provinsi Papua baru); (d) robots.txt/ketentuan penggunaan situs BI. Jika (a) gagal → Q4 memakai rata-rata provinsi equal-weight, catat keputusannya.
- [ ] **Step 3:** Isi keempat CSV referensi (nama provinsi `pihps_id` cocok persis dengan `GetRefProvince`; sumber + tanggal akses tiap file di `DATA_SOURCES.md`). Jika tabel BPS tidak bisa diambil otomatis, minta user mengunduh xlsx BPS dan sebutkan URL-nya.
- [ ] **Step 4: Tulis `tests/test_reference.py`:** `test_provinces_unique_ids` (pihps_id & bps_code unik), `test_provinces_enums` (tz_region & island_group dalam set di atas, lat ∈ [-11, 6], lon ∈ [95, 141]), `test_holidays_one_per_year_2018_2026`, `test_ump_complete` (setiap provinsi punya UMP untuk setiap tahun ≥ `valid_from_year`, nilai > 1_000_000), `test_basket_ids_exist` (setiap `commodity_id` berbentuk `com_<n>` dengan 1 ≤ n ≤ 21).
- [ ] **Step 5:** `uv run pytest tests/test_reference.py -v` → PASS.
- [ ] **Step 6:** Commit `chore: scaffold project and reference data`.

### Task 2: PIHPS client + extractor dengan resume

**Files:**
- Create: `src/pangan/pihps_client.py`, `src/pangan/extract.py`
- Test: `tests/test_client.py`, `tests/test_extract.py`

**Interfaces:**
- Consumes: `pangan.config`.
- Produces:
  - `class PihpsClient(session: requests.Session | None = None, delay_s: float = REQUEST_DELAY_S, timeout_s: float = TIMEOUT_S, max_retries: int = MAX_RETRIES, sleep: Callable[[float], None] = time.sleep)` dengan `get_provinces() -> list[dict]`, `get_commodities() -> list[dict]`, `get_price_grid(price_type_id: int, province_id: int | None, start: date, end: date) -> dict` (selalu meminta `comcat_id=cat_1,...,cat_10`; `None` → `province_id=""`). Retry pada timeout/ConnectionError/5xx; 4xx langsung raise.
  - `@dataclass(frozen=True) class Job(price_type_id: int, province_id: int | None, year: int)` dengan `.date_range() -> tuple[date, date]` (dipotong ke START_DATE/END_DATE) dan `.cache_path(raw_dir: Path) -> Path` = `raw_dir/f"pt{price_type_id}"/f"prov{province_id or 'national'}"/f"{year}.json"`.
  - `build_jobs(province_ids: list[int], years: range) -> list[Job]`: Pasar Tradisional (pt=1) per provinsi per tahun + pt 1–4 nasional per tahun.
  - `run_extract(client: PihpsClient, jobs: list[Job], raw_dir: Path) -> int` (jumlah job yang di-fetch): skip jika cache ada; tulis ke `*.json.tmp` lalu `os.replace`; simpan juga `raw_dir/ref_provinces.json`, `ref_commodities.json`; log progres + ETA.

- [ ] **Step 1: Tulis test yang gagal.** `tests/test_client.py` memakai fake session (tanpa jaringan), `delay_s=0`, `sleep=lambda s: None`:
  - `test_retries_then_succeeds`: dua respons 500 lalu 200 → hasil = JSON dari 200, total 3 panggilan.
  - `test_raises_after_max_retries`: selalu 500 → raise setelah `max_retries + 1` panggilan.
  - `test_4xx_not_retried`: 404 → raise setelah 1 panggilan.
  - `test_national_sends_empty_province`: `province_id=None` → param `province_id == ""`, `comcat_id == "cat_1,cat_2,...,cat_10"`, `tipe_laporan == 1`.

  `tests/test_extract.py`:
  - `test_build_jobs_count`: `build_jobs([1, 13], range(2018, 2020))` → 4 job provinsi + 8 job nasional = 12.
  - `test_last_year_clipped`: `Job(1, 13, 2026).date_range() == (date(2026,1,1), date(2026,9,30))`.
  - `test_resume_skips_cached`: satu cache sudah ada → fake client hanya dipanggil untuk job sisanya; return value = jumlah job yang di-fetch.
  - `test_no_partial_file_on_failure`: client raise di tengah → tidak ada file `*.tmp` atau `.json` untuk job yang gagal.
- [ ] **Step 2:** `uv run pytest tests/test_client.py tests/test_extract.py -v` → FAIL (modul belum ada).
- [ ] **Step 3:** Implement kedua modul sesuai signature di atas.
- [ ] **Step 4:** Test → PASS.
- [ ] **Step 5:** Commit `feat: add polite PIHPS client and resumable extractor`.
- [ ] **Step 6: Mulai download penuh di background** (setelah Task 6 Step 1 menambah CLI; bila CLI belum ada, jalankan `uv run python -c "from pangan.extract import main; main()"` dengan `main()` tipis di `extract.py` yang memanggil `build_jobs` dengan semua `pihps_id` dari `provinces.csv` dan `range(START_DATE.year, END_DATE.year + 1)`). Lanjutkan Task 3–5 dengan fixture selama download berjalan.

### Task 3: Transform (parsing + wide→long)

**Files:**
- Create: `src/pangan/transform.py`, `tests/fixtures/grid_sample.json`
- Test: `tests/test_transform.py`

**Interfaces:**
- Produces:
  - `parse_price(raw: str | None) -> int | None`: `"16,150"→16150`, `"1,234,567"→1234567`, `" 16,150 "→16150`, `"-"`/`""`/`None` → `None`; format lain (mis. `"16.150,5"`, `"abc"`) → `ValueError`.
  - `parse_grid_date(col: str) -> date`: format `%d/%m/%Y` saja.
  - `grid_to_long(payload: dict, *, province_id: int, market_type_id: int, commodity_lookup: dict[str, str]) -> pd.DataFrame` dengan kolom `[date_key (datetime64), province_id (int32), commodity_id (str), market_type_id (int8), price_idr (int64)]`; hanya baris `level == 2`; nama di-`strip()` sebelum lookup; nama tak dikenal → `KeyError`; harga `None` dibuang. `province_id=0` untuk nasional.
  - `commodity_lookup_from_ref(ref: list[dict]) -> dict[str, str]` (nama ter-strip → `com_*`, hanya id `com_`).

- [ ] **Step 1:** Buat fixture dari bentuk response yang sudah diverifikasi: 1 baris level 1 `"Beras"`, 2 baris level 2 (`"Beras Kualitas Bawah I"`, `"Cabai Merah Keriting "`), kolom `"01/03/2024"` dan `"04/03/2024"`, satu nilai `"-"`.
- [ ] **Step 2: Tulis test yang gagal:**
  - `test_parse_price_cases` (semua contoh di atas, termasuk `pytest.raises(ValueError)`).
  - `test_parse_grid_date_day_first`: `parse_grid_date("01/03/2024") == date(2024, 3, 1)`.
  - `test_grid_to_long_shape`: fixture → 3 baris (2 komoditas × 2 tanggal − 1 nilai `"-"`), tidak ada baris kategori, dtype sesuai.
  - `test_grid_to_long_strips_names`: `"Cabai Merah Keriting "` terpetakan.
  - `test_grid_to_long_empty`: `{"data": []}` → DataFrame 0 baris dengan 5 kolom di atas.
  - `test_grid_to_long_unknown_name_raises`.
- [ ] **Step 3:** Run → FAIL. **Step 4:** Implement. **Step 5:** Run → PASS.
- [ ] **Step 6:** Commit `feat: add PIHPS grid transform`.

### Task 4: Warehouse DuckDB + data quality

**Files:**
- Create: `sql/schema.sql`, `sql/views.sql`, `src/pangan/warehouse.py`, `src/pangan/quality.py`
- Test: `tests/test_warehouse.py` (+ `tests/conftest.py` fixture `raw_dir` mini: ref JSON + 2 file cache kecil)

**Interfaces:**
- Consumes: `transform.grid_to_long`, `commodity_lookup_from_ref`, `config`.
- Produces:
  - Tabel: `dim_date(date_key DATE PK, year, month, iso_week, dow, idul_fitri DATE, lebaran_year INT, days_to_lebaran INT, is_ramadan BOOL)`; `dim_province(province_id INT PK, province_name, bps_code, island_group, tz_region, capital, lat, lon, is_national BOOL)` (+ baris `0, 'Indonesia (Nasional)'`); `dim_commodity(commodity_id PK, commodity_name, category_id, category_name, unit)`; `dim_market_type(market_type_id PK, name, chain_order)` dengan `chain_order`: Produsen 1, Pedagang Besar 2, Pasar Tradisional 3, Pasar Modern 4; `fact_price_daily(date_key, province_id, commodity_id, market_type_id, price_idr BIGINT, is_outlier BOOL, PRIMARY KEY(date_key, province_id, commodity_id, market_type_id))`; `ref_ump(bps_code, year, ump_idr)`, `ref_basket(commodity_id, qty_kg_per_capita_week)`.
  - `dim_date`: semua hari kalender START..END; `days_to_lebaran = date_key − idul_fitri` terdekat, hanya jika dalam `LEBARAN_WINDOW` (−90..+45), selain itu NULL (begitu juga `idul_fitri`, `lebaran_year`); `is_ramadan = days_to_lebaran BETWEEN -30 AND -1` (aproksimasi, dicatat di PENJELASAN).
  - Outlier: `is_outlier = price / median(price) per (province, commodity, market_type, year-month) > OUTLIER_RATIO atau < 1/OUTLIER_RATIO`.
  - Views: `v_price_province` (fact ⨝ dims, `NOT is_outlier AND NOT is_national`), `v_price_national` (`NOT is_outlier AND is_national`).
  - `build_warehouse(raw_dir: Path, ref_dir: Path, db_path: Path) -> None` (idempoten: hapus & bangun ulang). Path cache `pt{n}/prov{id|national}/{year}.json` → `market_type_id = n`, `province_id = id` atau `0` untuk `national`.
  - `quality_report(con) -> dict[str, object]` dengan key `rows, duplicate_keys, null_prices, outliers, coverage` (`coverage`: DataFrame `province_name, year, pct_business_days` untuk pt=1).

- [ ] **Step 1: Tulis test yang gagal** (`tests/test_warehouse.py`, DB di `tmp_path`):
  - `test_build_creates_tables_and_rows`: semua tabel di atas ada, `fact_price_daily` > 0 baris.
  - `test_primary_key_unique`: `quality_report(con)["duplicate_keys"] == 0`.
  - `test_outlier_flagged_and_excluded`: fixture menyisipkan satu harga 10× median → `is_outlier` TRUE untuk baris itu, dan baris itu tidak muncul di `v_price_province`.
  - `test_national_separated`: `province_id = 0` tidak ada di `v_price_province`, ada di `v_price_national`.
  - `test_dim_date_lebaran`: `2024-04-03` → `days_to_lebaran == -7`, `is_ramadan`; `2024-01-01` → `days_to_lebaran IS NULL` (di luar window −90).
  - `test_empty_cache_file_ok`: file cache `{"data": []}` untuk satu provinsi → build sukses, coverage provinsi itu 0.
- [ ] **Step 2:** Run → FAIL. **Step 3:** Implement (load pandas → `con.register` → `INSERT`; outlier via `UPDATE ... FROM` subquery median). **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit `feat: build DuckDB star schema with quality checks`.

### Task 5: Mart SQL Q1–Q5

**Files:**
- Create: `sql/marts/q1_lebaran.sql`, `q2_volatility.sql`, `q3_disparity.sql`, `q4_supply_chain.sql`, `q5_affordability.sql`, `src/pangan/marts.py`
- Test: `tests/test_marts.py` (warehouse sintetis dibuat langsung via SQL di fixture, tidak lewat raw)

**Interfaces:**
- Produces: `build_marts(con, sql_dir: Path = SQL_DIR / "marts") -> list[str]` (jalankan file urut nama; return nama tabel `mart_*` yang ada). Setiap file `CREATE OR REPLACE TABLE`:
  - `mart_q1_lebaran_index(commodity_id, lebaran_year, t, price_idr, price_index)`: seri nasional Pasar Tradisional, `t` = `days_to_lebaran` ∈ [−60, 30], `price_index = price / AVG(price pada t ∈ [−60, −46])` per (komoditas, tahun). `mart_q1_summary(commodity_id, median_peak_pct, median_peak_t, median_start_rise_t, n_years)`: per tahun ambil `max(price_index) − 1` dan `t` di puncak (`arg_max`), `start_rise_t` = `t` pertama dengan index ≥ 1.05; lalu median antartahun.
  - `mart_q2_weekly(commodity_id, week, price_idr, pct_1w, pct_4w)` (rata-rata mingguan nasional pt=1, `LAG`), `mart_q2_volatility(commodity_id, year, std_pct_1w)`, `mart_q2_top_shocks(commodity_id, week, pct_4w, rank)` (top 5 `pct_4w` per komoditas).
  - `mart_q3_province_index(province_id, commodity_id, month, avg_price, index_vs_median)` (rata-rata bulanan / median antarprovinsi bulan itu), `mart_q3_disparity(commodity_id, month, cv)` (`stddev_samp/avg` antarprovinsi).
  - `mart_q4_markup(commodity_id, month, from_level, to_level, markup_pct)` antar `chain_order` berurutan; hanya bulan yang kedua levelnya ada.
  - `mart_q5_affordability(province_id, year, month, basket_cost_idr, ump_idr, share_of_ump)`: `basket_cost = Σ avg_month_price × qty_kg_per_capita_week × 52/12 × HOUSEHOLD_SIZE`; hanya (provinsi, bulan) dengan **semua** item keranjang tersedia, dan `INNER JOIN` UMP.
  - `HOUSEHOLD_SIZE` dimasukkan ke SQL sebagai parameter (`SET VARIABLE household_size = 4` dari `marts.py`), bukan hardcode.

- [ ] **Step 1: Tulis test yang gagal** (data sintetis, satu komoditas kecuali disebut):
  - `test_q1_baseline_and_peak`: harga 100 di t ∈ [−60, −46], 120 di t = −7 → `price_index` di t = −7 == 1.2; rata-rata index pada baseline == 1.0; `median_peak_pct ≈ 0.20`, `median_peak_t == -7`.
  - `test_q4_markup`: produsen 10_000, pedagang besar 12_000, tradisional 15_000, modern 16_500 → markup 0.20, 0.25, 0.10 (approx).
  - `test_q5_share`: 2 item keranjang, harga 10_000 (qty 1.0) dan 20_000 (qty 0.5), UMP 3_466_667 → `basket_cost ≈ 346_666.67`, `share_of_ump ≈ 0.10` (rel 1e-4).
  - `test_q5_excludes_incomplete`: satu item hilang di bulan tertentu → bulan itu tidak ada di mart; provinsi tanpa UMP → tidak ada di mart.
  - `test_all_marts_run`: `build_marts` mengembalikan ke-9 nama tabel `mart_*` di atas.
- [ ] **Step 2:** Run → FAIL. **Step 3:** Tulis SQL (CTE + window function, gaya mudah dibaca, komentar singkat per CTE). **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit `feat: add analysis marts for five business questions`.

### Task 6: CLI + menjalankan pipeline dengan data nyata

**Files:**
- Create: `src/pangan/cli.py`; Modify: `pyproject.toml` (`[project.scripts] pangan = "pangan.cli:main"`)
- Test: `tests/test_cli.py`

**Interfaces:**
- Produces: `main(argv: list[str] | None = None) -> int` dengan subcommand `extract`, `build`, `marts`, `export` (dipanggil dari Task 8), `quality` (cetak `quality_report`), `all` (extract → build → marts → export).

- [ ] **Step 1:** Test `test_cli_dispatch` (monkeypatch fungsi tiap subcommand, assert yang benar terpanggil; `all` memanggil berurutan). Run → FAIL → implement → PASS. Commit `feat: add pangan CLI`.
- [ ] **Step 2:** Pastikan download background (Task 2 Step 6) selesai; jalankan ulang `uv run pangan extract` → output "0 jobs fetched" (bukti resume lengkap).
- [ ] **Step 3:** `uv run pangan build` lalu `uv run pangan quality` → catat `rows` (perkiraan ±2 juta), `duplicate_keys == 0`, `null_prices == 0`, jumlah outlier, provinsi dengan coverage rendah. Simpan ringkasan ke `docs/DATA_SOURCES.md` bagian "Data quality".
- [ ] **Step 4:** `uv run pangan marts` → semua 9 mart terisi (`SELECT COUNT(*)` > 0 tiap tabel). Jika ada mart kosong (mis. Produsen tidak tersedia untuk komoditas tertentu), catat dan sesuaikan narasi, bukan memalsukan data.

### Task 7: Notebook analisis + figur

**Files:**
- Create: `notebooks/01_data_quality.ipynb`, `notebooks/02_analysis.ipynb`, `src/pangan/plots.py`, `reports/figures/*.png`
- Test: `tests/test_plots.py`

**Interfaces:**
- Consumes: `WAREHOUSE_PATH`, tabel `mart_*`, `quality_report`.
- Produces: `plots.py` fungsi kecil yang return `matplotlib.figure.Figure`: `plot_lebaran_index(df, commodity_id)`, `plot_volatility(df)`, `plot_province_index(df, commodity_id)`, `plot_markup(df)`, `plot_affordability(df)`; helper `save_fig(fig, name) -> Path` ke `FIG_DIR`.

- [ ] **Step 1:** Load skill `dataviz`; terapkan palet & aturannya di `plots.py`.
- [ ] **Step 2:** `tests/test_plots.py::test_plots_return_figures` — tiap fungsi dengan DataFrame sintetis kecil → `isinstance(fig, Figure)` dan ada judul + label sumbu. Run → FAIL → implement → PASS.
- [ ] **Step 3:** `01_data_quality.ipynb`: coverage heatmap provinsi × tahun, jumlah outlier per komoditas, contoh outlier, penjelasan keputusan cleaning.
- [ ] **Step 4:** `02_analysis.ipynb`: per pertanyaan → query mart → chart → markdown "Temuan" + "Rekomendasi" yang ditulis **dari angka yang keluar**. Statistik: bootstrap CI 95% (`numpy`, 10_000 resample, seed 42) untuk `median_peak_pct` antartahun (sebutkan n tahun kecil); `scipy.stats.spearmanr` untuk tren CV disparitas per komoditas. Hindari klaim kausal.
- [ ] **Step 5:** `uv run jupyter nbconvert --to notebook --execute --inplace notebooks/01_data_quality.ipynb notebooks/02_analysis.ipynb` → tanpa error; figur tersimpan di `reports/figures/`.
- [ ] **Step 6:** Commit `feat: add quality and analysis notebooks with figures`.

### Task 8: Export Tableau + panduan dashboard

**Files:**
- Create: `src/pangan/export.py`, `exports/tableau/*.csv`, `docs/TABLEAU_GUIDE.md`
- Test: `tests/test_export.py`

**Interfaces:**
- Produces: `export_tableau(con, out_dir: Path = EXPORT_DIR) -> list[Path]`, menulis CSV UTF-8 dengan nama yang mudah dibaca (join ke `commodity_name, province_name, tz_region, island_group, lat, lon`): `lebaran_index.csv, lebaran_summary.csv, weekly_national.csv, volatility.csv, top_shocks.csv, province_index.csv, disparity_trend.csv, supply_chain_markup.csv, affordability.csv, price_weekly_province.csv`.

- [ ] **Step 1:** `test_export_files` (warehouse sintetis dari Task 5 → 10 file ada, header berisi `commodity_name`, tanpa kolom id mentah saja). Run → FAIL → implement → PASS.
- [ ] **Step 2:** `uv run pangan export`; cek ukuran file (aturan 50 MB di Global Constraints).
- [ ] **Step 3:** Tulis `docs/TABLEAU_GUIDE.md` (Bahasa Indonesia, langkah demi langkah dengan nama field persis): instal Tableau Public, connect CSV, 4 dashboard — (1) Overview & Explorer (tren mingguan, filter provinsi/komoditas, KPI harga terakhir & YoY), (2) Efek Lebaran (garis index t −60..+30 per tahun + median), (3) Peta Disparitas (peta simbol lat/lon, warna divergen di 1.0, bar per tz_region), (4) Rantai Pasok & Keterjangkauan; teks atribusi sumber; cara publish & ambil link.
- [ ] **Step 4:** Commit `feat: export Tableau datasets and dashboard guide`.

### Task 9: README, PENJELASAN, CV, verifikasi akhir

**Files:**
- Create: `README.md`, `docs/PENJELASAN.md`, `docs/CV_BULLETS.md`

- [ ] **Step 1:** `README.md` (Inggris): judul, 1 paragraf masalah bisnis (skenario fiktif disebut jelas), **Key Findings** (3–5 butir berangka dari mart), **Recommendations**, figur utama, placeholder `TABLEAU_PUBLIC_URL` yang jelas ditandai untuk diisi user, arsitektur (diagram alur teks), cara menjalankan (`uv sync`, `uv run pangan all`, catatan durasi ±4–5 jam), struktur repo, keterbatasan (data hari kerja, aproksimasi Ramadan, keranjang berbasis rata-rata Susenas, endpoint tidak resmi), atribusi sumber.
- [ ] **Step 2:** `docs/PENJELASAN.md` (Indonesia): penjelasan tiap modul/SQL — apa, kenapa, alternatif yang ditolak; tabel "asal angka" (setiap angka README → query mart-nya); ±15 pertanyaan interview + jawaban (star schema, kenapa DuckDB, window function di Q2/Q3, penanganan outlier, kenapa median, keterbatasan bootstrap n kecil, scraping etis, dll.).
- [ ] **Step 3:** `docs/CV_BULLETS.md`: 3 bullet (Inggris + Indonesia) dengan angka nyata (jumlah baris, provinsi, temuan utama).
- [ ] **Step 4: Verifikasi akhir:** `uv run pytest -q` (semua PASS), `uv run ruff check .` (bersih), `uv run pangan build && uv run pangan marts && uv run pangan export` dari cache (sukses), eksekusi ulang kedua notebook tanpa error, cocokkan setiap angka README dengan tabel "asal angka".
- [ ] **Step 5:** Commit `docs: add README, explainer, and CV bullets`.

### Task 10: Langkah manual user (dengan panduan Claude)

- [ ] User membuat dashboard mengikuti `docs/TABLEAU_GUIDE.md`, publish ke Tableau Public, berikan link → Claude mengganti `TABLEAU_PUBLIC_URL` di README dan commit.
- [ ] User membuat repo GitHub publik `harga-pangan-indonesia`; **Claude minta konfirmasi dulu** sebelum `git remote add` / `git push`.

---

## Verifikasi end-to-end

1. `uv run pytest -q` → semua test PASS (reference, client, extract, transform, warehouse, marts, cli, plots, export).
2. `uv run pangan extract` kedua kali → 0 job di-fetch (cache lengkap); `uv run pangan quality` → `duplicate_keys = 0`, `null_prices = 0`.
3. `uv run pangan marts && uv run pangan export` → 9 mart terisi, 10 CSV di `exports/tableau/`.
4. Kedua notebook dieksekusi ulang via `nbconvert --execute` tanpa error; figur ada di `reports/figures/`.
5. Setiap angka di README dapat dilacak ke query di tabel "asal angka" `PENJELASAN.md`.

## Di luar scope

Projek 2 (kualitas udara multi-kota: Open-Meteo CAMS + data stasiun AQICN/Satu Data, dashboard Looker Studio/Power BI), data level kabupaten/kota, forecasting/ML, deploy otomatis/penjadwalan update data.
