# CV bullets — Harga Pangan Indonesia

Pick 2–3. Every number is traceable to `docs/PENJELASAN.md` § 3.

## English

**Indonesian Food Price Analysis (2018–2026)** — Python, SQL (DuckDB), Tableau · [github.com/Alb138/harga-pangan-indonesia](https://github.com/Alb138/harga-pangan-indonesia)

- Built an end-to-end pipeline that collects **1.7M daily prices** for 21 staple foods across
  34 provinces from Bank Indonesia's PIHPS, models them in a DuckDB star schema and answers four
  procurement questions with SQL window functions; 76 automated tests.
- Found and fixed data issues hidden in the source — a 22-day price typo and holiday days where
  1–2 provinces stood in for the "national" price — using a rolling-median outlier rule and
  coverage filters, removing a fake 13% rice spike.
- Showed that only chicken (+12.8%, 95% CI 7.5–17.5%) and eggs rise reliably before Lebaran,
  chillies are 17–30× more volatile than rice, and eastern provinces pay up to 52% more;
  turned this into timing, contract and sourcing recommendations in a Tableau dashboard.

## Bahasa Indonesia

**Analisis Harga Pangan Indonesia (2018–2026)** — Python, SQL (DuckDB), Tableau · [github.com/Alb138/harga-pangan-indonesia](https://github.com/Alb138/harga-pangan-indonesia)

- Membangun pipeline end-to-end yang mengumpulkan **1,7 juta harga harian** 21 komoditas pangan
  di 34 provinsi dari PIHPS Bank Indonesia, memodelkannya dalam star schema DuckDB, dan menjawab
  empat pertanyaan procurement dengan SQL window function; 76 test otomatis.
- Menemukan dan memperbaiki masalah tersembunyi di sumber data — salah ketik harga selama 22 hari
  dan hari libur ketika 1–2 provinsi mewakili harga "nasional" — dengan aturan outlier median
  bergulir dan filter coverage, menghapus lonjakan harga beras palsu 13%.
- Menunjukkan bahwa hanya ayam (+12,8%, CI 95% 7,5–17,5%) dan telur yang naik konsisten menjelang
  Lebaran, cabai 17–30× lebih volatil dari beras, dan provinsi timur membayar hingga 52% lebih
  mahal; dituangkan menjadi rekomendasi waktu beli, kontrak, dan sumber pasokan di dashboard
  Tableau.
