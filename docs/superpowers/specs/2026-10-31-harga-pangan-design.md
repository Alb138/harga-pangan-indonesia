# Harga Pangan Indonesia — Design Spec (disetujui 2026-10-31)

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

