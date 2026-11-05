# Penjelasan Projek — Harga Pangan Indonesia

Dokumen ini menjelaskan **apa** yang dikerjakan setiap bagian projek, **kenapa** dibuat begitu,
dan **alternatif** yang tidak dipilih. Baca dari atas ke bawah satu kali sebelum interview,
lalu pakai bagian *Pertanyaan Interview* sebagai latihan.

---

## 1. Gambaran besar

```
PIHPS (Bank Indonesia) → extract → transform → warehouse DuckDB → mart SQL → notebook + Tableau
```

| Tahap | File | Satu kalimat |
|---|---|---|
| Ambil data | `src/pangan/pihps_client.py`, `extract.py` | Mengunduh harga harian dari endpoint JSON PIHPS, satu request per waktu, disimpan sebagai cache. |
| Bersihkan | `src/pangan/transform.py` | Mengubah tabel "lebar" (satu kolom per tanggal) menjadi baris rapi (tanggal, provinsi, komoditas, pasar, harga). |
| Simpan | `src/pangan/warehouse.py`, `sql/schema.sql` | Memuat data ke database DuckDB berbentuk *star schema* dan menandai data yang salah. |
| Analisis | `sql/marts/q1…q5.sql` | Satu file SQL per pertanyaan bisnis, hasilnya tabel `mart_*`. |
| Cerita | `notebooks/02_analysis.ipynb` | Chart, uji statistik sederhana, temuan, dan rekomendasi. |
| Dashboard | `src/pangan/export.py`, `docs/TABLEAU_GUIDE.md` | CSV siap Tableau + panduan membuat dashboard. |

Semua dijalankan dengan satu perintah: `uv run pangan all`.

---

## 2. Setiap tahap

### 2.1 Mengambil data (extract)

**Apa:** PIHPS tidak punya API resmi. Halaman tabel harganya mengambil data dari endpoint JSON
(`GetGridDataDaerah`). Kita memanggil endpoint yang sama: satu request = satu jenis pasar ×
satu provinsi × satu tahun × semua komoditas. Totalnya 342 request.

**Kenapa begini:**
- **Sopan ke server:** berurutan (tidak paralel), jeda 2 detik, User-Agent yang jujur. Server
  BI lambat (±40 detik per request); kalau dibanjiri request paralel, kita bisa diblokir — dan itu
  tidak etis.
- **Cache + resume:** setiap respons disimpan ke `data/raw/`. Kalau terputus (terminal ditutup,
  laptop mati), menjalankan ulang hanya mengunduh yang belum ada. Ini terjadi sungguhan di projek
  ini — download terputus dua kali dan bisa dilanjutkan tanpa mengulang.
- **Tulis atomik:** file ditulis ke `*.tmp` lalu di-*rename*. Kalau proses mati di tengah, tidak
  ada file JSON setengah jadi yang nanti dikira data lengkap.
- **Retry hanya untuk error sementara:** timeout, error 5xx, dan — ditemukan dari data nyata —
  respons `200 OK` yang isinya kosong. Error 4xx (request kita salah) tidak di-retry.

**Alternatif yang ditolak:** scraping HTML dengan Selenium (lebih lambat dan rapuh), atau dataset
WFP/World Bank (hanya bulanan, sehingga efek Lebaran yang bergeser ±11 hari per tahun jadi kabur).

### 2.2 Membersihkan (transform)

Respons PIHPS bentuknya *wide*:

```json
{"name": "Cabai Merah Keriting ", "level": 2, "01/03/2024": "66,800", "04/03/2024": "-"}
```

Masalah yang ditangani `transform.py`:

| Masalah | Penanganan |
|---|---|
| Harga berupa teks `"16,150"` | `parse_price` → 16150. Format yang tidak dikenal **melempar error**, tidak ditebak. |
| `"-"` = tidak dilaporkan | Dibuang (bukan diisi 0 — 0 akan merusak rata-rata). |
| Tanggal `"01/03/2024"` | Dibaca **day-first** → 1 Maret, bukan 3 Januari. Ada test khususnya. |
| Nama berspasi di akhir (`"Cabai Merah Keriting "`) | Di-`strip()` sebelum dicocokkan ke id komoditas. |
| Baris kategori (level 1) | Dibuang; rata-rata kategori bisa dihitung ulang sendiri. |

Prinsipnya: **gagal dengan keras** daripada diam-diam salah. Nama komoditas yang tidak dikenal
melempar `KeyError`, supaya perubahan di sumber langsung ketahuan.

### 2.3 Warehouse (DuckDB, star schema)

```
                dim_date ─┐
            dim_province ─┼── fact_price_daily (1.713.633 baris)
           dim_commodity ─┤   grain: 1 harga per (tanggal, provinsi, komoditas, jenis pasar)
         dim_market_type ─┘
```

- **Kenapa star schema:** fakta (harga) dipisah dari atribut (nama provinsi, wilayah waktu,
  urutan rantai pasok, jarak ke Lebaran). Query analisis jadi pendek dan atribut cukup diubah di
  satu tempat.
- **`dim_date`** menyimpan `days_to_lebaran` (H-7 = −7) dan `is_ramadan`. Analisis Lebaran cukup
  `JOIN dim_date` — tidak perlu menghitung tanggal di setiap query.
- **Primary key** di tabel fakta menjamin tidak ada harga ganda untuk kunci yang sama.
- **Kenapa DuckDB:** database analitik di dalam satu file — tidak perlu install server, cukup
  `uv sync`. Orang yang meng-clone repo bisa langsung menjalankannya. SQL-nya standar (CTE, window
  function), jadi mudah dipindah ke PostgreSQL atau BigQuery.

**Dua aturan pembersihan yang ditemukan dari data nyata** (cerita bagus untuk interview):

1. **Outlier = harga lebih dari 3× di atas/bawah median ±60 hari di sekitarnya.**
   Versi pertama memakai median *bulanan*. Lalu di data ditemukan harga produsen daging sapi
   tercatat ±Rp583.000 (seharusnya ±Rp108.000) selama 22 hari kerja (20 Sep – 19 Okt 2021). Di
   bulan Oktober, harga salah itu justru mayoritas — jadi median bulanan *adalah* harga yang salah,
   dan yang ditandai malah harga yang benar. Median bergulir ±60 hari menandai tepat 22 hari itu.
   Total 33 harga ditandai dan dikeluarkan dari analisis.
2. **Hari "tipis" dikeluarkan dari seri nasional.** Saat libur Lebaran 2022 hanya 1–2 dari 34
   provinsi yang melapor, tapi PIHPS tetap menerbitkan harga "nasional" — padahal itu harga 1–2
   provinsi saja. Hasilnya beras seolah naik 13% dalam seminggu. Hari dengan < 50% provinsi
   melapor (77 hari kerja) dikeluarkan dari seri nasional; data provinsinya tetap dipakai.

### 2.4 Analisis SQL (mart)

Setiap pertanyaan = satu file SQL yang membuat tabel `mart_*`. Teknik SQL yang dipakai:

| Teknik | Di mana | Untuk apa |
|---|---|---|
| CTE (`WITH ...`) | semua mart | memecah query panjang jadi langkah yang bisa dibaca |
| Window `LAG()` | `q2_volatility.sql` | perubahan harga 1 dan 4 minggu |
| Window `median() OVER (PARTITION BY ...)` | `q3_disparity.sql`, `load_fact.sql` | median antarprovinsi per bulan; median bergulir ±60 hari |
| `RANGE BETWEEN INTERVAL ...` | `load_fact.sql` | jendela waktu berdasarkan tanggal, bukan jumlah baris |
| `QUALIFY row_number() ...` | `q2_volatility.sql` | ambil top-5 lonjakan, maksimal satu per bulan |
| `arg_max()`, `FILTER (WHERE ...)` | `q1_lebaran.sql` | minggu puncak; minggu pertama indeks ≥ 1,05 |
| Self-join | `q4_supply_chain.sql` | membandingkan level rantai pasok yang berurutan |

**Q1 – Lebaran.** Indeks = harga ÷ rata-rata harga H-60 s.d. H-46 tahun yang sama (sebelum efek
Ramadan). Besar kenaikan = median dari puncak tiap tahun. Waktunya (mulai naik, puncak, normal
lagi) dibaca dari **satu kurva musim tipikal** (median antartahun dari rata-rata mingguan).
Versi pertama mengambil median *tiap angka* secara terpisah dan hasilnya bertentangan (bawang
merah: puncak H+12 tapi "normal lagi" H-40) — makanya diganti.

**Q2 – Volatilitas.** Standar deviasi perubahan harga mingguan. Lonjakan terbesar = perubahan 4
minggu tertinggi, satu per bulan supaya satu lonjakan panjang tidak memenuhi seluruh daftar.

**Q3 – Disparitas.** Indeks = harga provinsi ÷ **median** provinsi bulan itu. Median dipakai
(bukan rata-rata) karena Papua yang sangat mahal akan menarik rata-rata ke atas. Ketimpangan
diukur dengan *coefficient of variation* (simpangan baku ÷ rata-rata) — tidak bergantung satuan
harga, sehingga cabai dan beras bisa dibandingkan.

**Q4 – Rantai pasok.** Persentase kenaikan antar level berurutan (Produsen → Pedagang Besar →
Pasar Tradisional → Pasar Modern). Catatan: pasar modern bukan tahap setelah pasar tradisional,
melainkan saluran ritel alternatif.

**Q5 – Keterjangkauan.** Biaya keranjang sembako rumah tangga 4 orang (jumlah konsumsi per
kapita dari Susenas BPS) ÷ UMP provinsi. Hanya bulan dengan **semua** item tersedia yang dihitung —
keranjang yang tidak lengkap akan terlihat murah palsu. *Status: menunggu data BPS (API key).*

### 2.5 Statistik di notebook

- **Bootstrap CI 95%** untuk median kenaikan Lebaran: dari 9 musim, ambil sampel ulang 10.000 kali
  dan lihat sebaran mediannya. Kalau intervalnya mencakup 0 (cabai rawit merah: −4,5% s.d. +52%),
  kenaikannya **tidak konsisten** — jangan dijadikan dasar keputusan.
- **Korelasi Spearman** antara waktu dan CV bulanan: ρ negatif = ketimpangan menyempit. Spearman
  dipakai karena hanya butuh tren monoton, tidak harus garis lurus.
- Semua hasil bersifat **deskriptif**, bukan sebab-akibat.

### 2.6 Visualisasi

- Garis tipis, grid tipis, satu sumbu Y, maksimal 3 warna kategori per chart.
- Chart Lebaran: tiap tahun abu-abu, median biru — 9 tahun dengan 9 warna akan tidak terbaca.
- Peta/bar disparitas: skala divergen biru (lebih murah) ↔ merah (lebih mahal) dengan titik
  tengah abu-abu di median.
- Setiap chart mencantumkan sumber data.

### 2.7 Test

74 test (`uv run pytest`) memakai data sintetis kecil dengan angka yang bisa dihitung manual —
misalnya harga produsen 10.000 → pedagang besar 12.000 harus menghasilkan markup tepat 20%.
Setiap bug yang ditemukan dari data nyata **pertama dibuat test-nya yang gagal**, baru diperbaiki.

---

## 3. Asal setiap angka di README

| Angka di README | Dari mana |
|---|---|
| 1.713.633 baris, 33 outlier, 77 hari tipis, coverage ≥ 92% | `uv run pangan quality`; `notebooks/01_data_quality.ipynb` |
| Ayam +12,8% (CI 7,5–17,5%), telur +8,1%, cabai rawit merah +17,7% (CI −4,5% s.d. +52,1%) | `mart_q1_summary.median_peak_pct`; CI dari sel bootstrap di `02_analysis.ipynb` |
| Beras/minyak/gula < 4% | `mart_q1_summary` (0,2%–3,7%) |
| Cabai rawit merah 8,5%/minggu vs beras ±0,3% | rata-rata `mart_q2_volatility.std_pct_1w` per komoditas |
| +125,5% (Des 2021), minyak +31–35% (Mar 2022), beras +6,2% (Feb 2024) | `mart_q2_top_shocks` (`rank = 1`) |
| Timur: cabai +52%, bawang merah +39%, telur +26%, beras +14% | rata-rata `mart_q3_province_index.index_vs_median` per `tz_region`, Okt 2025–Sep 2026 |
| Papua 1,28×, Sulsel 0,86× | rata-rata indeks semua komoditas per provinsi, 12 bulan terakhir |
| Telur ρ = −0,77, beras ρ = −0,74 | Spearman atas `mart_q3_disparity.cv` |
| Cabai produsen→pasar +46–60%, beras +15–21%, modern +42–72% | rata-rata `mart_q4_markup.markup_pct`, 12 bulan terakhir |

---

## 4. Pertanyaan interview (dan jawabannya)

**1. Ceritakan projek ini dalam 30 detik.**
Saya menganalisis 1,7 juta harga pangan harian dari Bank Indonesia untuk 34 provinsi selama 2018–
2026 dari sudut pandang tim procurement: kapan menyetok, komoditas apa yang perlu kontrak harga
tetap, di mana harga mahal, dan beli dari siapa. Datanya saya ambil sendiri, saya bersihkan di
DuckDB dengan star schema, analisisnya di SQL, dan hasilnya di notebook serta dashboard Tableau.
Temuan utamanya: hanya ayam dan telur yang naik konsisten saat Lebaran, cabai 17–30× lebih
volatil dari beras, dan wilayah timur membayar lebih mahal untuk semua 21 komoditas.

**2. Kenapa memilih data ini, bukan dataset Kaggle?**
Dataset populer (Titanic, Olist, Telco) sudah ribuan kali dianalisis. Data PIHPS relevan untuk
Indonesia, harus dikumpulkan dan dibersihkan sendiri — itu pekerjaan analis yang sebenarnya.

**3. Apa itu star schema dan kenapa dipakai?**
Satu tabel fakta berisi angka (harga) dengan kunci, dikelilingi tabel dimensi berisi atribut
(tanggal, provinsi, komoditas, jenis pasar). Query jadi sederhana dan atribut seperti jarak ke
Lebaran cukup dihitung sekali di `dim_date`.

**4. Kenapa DuckDB, bukan PostgreSQL?**
DuckDB adalah database analitik kolumnar dalam satu file: cepat untuk agregasi jutaan baris dan
tanpa server. Siapa pun bisa menjalankan repo ini dengan `uv sync`. SQL-nya standar sehingga
mudah dipindah ke PostgreSQL/BigQuery.

**5. Bagaimana kamu menangani data yang hilang?**
`"-"` berarti tidak dilaporkan; baris itu dibuang, bukan diisi 0 atau di-interpolasi, karena
mengisi akan mengarang data. Saya ukur coverage-nya: minimal 92% hari kerja per provinsi-tahun,
jadi tidak ada provinsi yang perlu dibuang.

**6. Bagaimana mendeteksi outlier, dan kenapa median?**
Harga dibandingkan dengan median ±60 hari di sekitarnya; lebih dari 3× di atas/bawah ditandai.
Median tahan terhadap nilai ekstrem — rata-rata justru ikut tertarik oleh outlier yang mau dicari.
Dan jendela bergulir, bukan bulanan, karena di data ada salah ketik yang berlangsung 22 hari
sehingga menjadi median bulan itu sendiri.

**7. Ceritakan bug yang kamu temukan.**
Harga beras "nasional" naik 13% dalam seminggu saat Lebaran 2022. Saya curiga karena beras
biasanya stabil, lalu cek data harian: ternyata di hari libur hanya 1–2 provinsi yang melapor,
jadi angka "nasional" hanyalah harga 1–2 provinsi. Saya buat test yang mereproduksinya, lalu
hari dengan kurang dari separuh provinsi melapor saya keluarkan dari seri nasional.

**8. Jelaskan window function di projek ini.**
`LAG(price, 4) OVER (PARTITION BY commodity_id ORDER BY week)` mengambil harga 4 minggu
sebelumnya untuk komoditas yang sama, untuk menghitung perubahan 4 minggu.
`median(price) OVER (PARTITION BY commodity, month)` menghitung median antarprovinsi tanpa
menghilangkan baris per provinsi — beda dengan `GROUP BY` yang meringkas baris.

**9. Kenapa membandingkan dengan median provinsi, bukan rata-rata nasional?**
Provinsi yang sangat mahal (Papua) menarik rata-rata ke atas, sehingga hampir semua provinsi
terlihat "lebih murah dari rata-rata". Median adalah provinsi yang tipikal.

**10. Seberapa yakin kamu bahwa ayam naik saat Lebaran?**
Median kenaikannya 12,8% dengan bootstrap CI 95% 7,5%–17,5% dari 9 musim. Intervalnya tidak
mencakup 0, jadi polanya konsisten. Untuk cabai intervalnya −4,5% s.d. +52%, jadi tidak bisa
disimpulkan. Catatan: 9 musim itu sampel kecil, intervalnya lebar.

**11. Korelasi bukan kausalitas — di mana itu berlaku di sini?**
Ketimpangan harga telur yang menyempit (ρ = −0,77) tidak membuktikan penyebabnya (infrastruktur,
kebijakan, dll). Saya hanya melaporkan bahwa trennya ada dan signifikan.

**12. Apa rekomendasi bisnis paling penting?**
Beli cabai, bawang, dan ayam dari pedagang besar, bukan pasar modern: tahap pedagang besar → pasar
menambah 16–29%, dan pasar modern 42–72% lebih mahal dari pasar tradisional untuk cabai dan bawang.

**13. Bagaimana kamu memastikan analisisnya benar?**
(1) 74 test dengan angka yang dihitung manual, (2) cek kualitas data (duplikat, null, outlier,
coverage), (3) mencocokkan hasil dengan peristiwa nyata — krisis minyak goreng Maret 2022 dan
lonjakan beras Februari 2024 muncul di data, (4) setiap angka di README bisa dilacak ke query-nya.

**14. Apakah scraping ini legal/etis?**
Datanya publik dan ditampilkan sendiri oleh Bank Indonesia; `robots.txt` BI mengizinkan
`/hargapangan`. Saya mengambil secara sopan (satu request per waktu, jeda, cache supaya tiap data
hanya diminta sekali) dan mencantumkan sumber di setiap chart.

**15. Apa yang akan kamu kembangkan selanjutnya?**
Menyelesaikan analisis keterjangkauan (sembako vs UMP), data tingkat kabupaten/kota, forecasting
harga cabai beberapa minggu ke depan, dan jadwal update otomatis.

---

## 5. Keterbatasan (sebutkan sendiri sebelum ditanya)

- Seri nasional PIHPS = rata-rata pasar yang melapor; hanya hari kerja.
- Ramadan diaproksimasi sebagai 30 hari sebelum Idul Fitri.
- 9 musim Lebaran adalah sampel kecil → interval kepercayaan lebar.
- Endpoint PIHPS tidak resmi dan bisa berubah; cache mentah disimpan agar analisis tetap bisa
  diulang.
