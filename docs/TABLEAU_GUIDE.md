# Panduan Membuat Dashboard di Tableau Public

Panduan ini membawa kamu dari file CSV di `exports/tableau/` sampai dashboard yang
dipublikasikan dengan link publik untuk CV. Semua nama field di bawah **persis sama**
dengan header CSV, jadi kamu tinggal seret (drag) field-nya.

> Waktu: ±3–4 jam untuk pertama kali. Simpan sering-sering (Tableau Public menyimpan ke cloud).

---

## 0. Persiapan

1. Unduh **Tableau Public** (gratis): <https://public.tableau.com/app/discover> → *Create* →
   *Download Tableau Public*. Buat akun dengan email-mu.
2. Pastikan CSV terbaru sudah ada: jalankan `uv run pangan export` di folder repo.
3. Buka Tableau Public → *Connect* → *To a File* → *Text file* → pilih
   `exports/tableau/price_weekly_province.csv`.
4. Tambahkan CSV lain sebagai **data source terpisah** (menu *Data → New Data Source*),
   satu per file. Kita tidak perlu join antar file — setiap sheet memakai satu sumber saja.

### Palet warna (pakai hex ini supaya konsisten dengan chart di notebook)

| Peran | Hex | Dipakai untuk |
|---|---|---|
| Biru (seri utama) | `#2a78d6` | garis/bar utama, "lebih murah" di peta |
| Oranye (seri 2) | `#eb6834` | seri kedua |
| Hijau aqua (seri 3) | `#1baf7a` | seri ketiga |
| Abu-abu | `#c3c2b7` | garis pembanding (tahun lain), sumbu |
| Merah | `#e34948` | "lebih mahal" di peta (ujung divergen) |
| Abu netral | `#f0efec` | titik tengah skala divergen (= median) |

Aturan singkat: maksimal 3 warna kategori per chart, garis tipis, gridline tipis abu-abu
(*Format → Lines → Grid Lines*), dan **satu sumbu Y saja** (jangan pakai dual axis dengan
skala berbeda).

Cara mengganti warna: klik kartu **Color** → *Edit Colors* → klik item → *More colors* →
isi hex.

---

## Dashboard 1 — Overview & Explorer

**Sumber:** `price_weekly_province.csv`

### Sheet "Tren Harga"
1. Seret `week` ke **Columns** → klik kanan → pilih **Week Number (continuous / hijau)**
   atau *Exact Date*.
2. Seret `avg_price_idr` ke **Rows** (otomatis `SUM`; ganti ke **Average**).
3. Seret `commodity_name` ke **Filters** → pilih satu komoditas (mis. *Cabai Rawit Merah*)
   → klik kanan filter → *Show Filter* → ubah jadi **Single Value (dropdown)**.
4. Seret `province_name` ke **Filters** → *Show Filter* → **Single Value (dropdown)**.
5. Warna garis: biru `#2a78d6`. *Format → Lines* → ketebalan tipis.
6. Format sumbu Y: klik kanan sumbu → *Format* → *Numbers* → *Currency (Custom)*, prefix
   `Rp `, 0 desimal.
7. Judul sheet: `Harga mingguan <commodity_name> di <province_name>` (klik kanan judul →
   *Edit Title* → *Insert* untuk menyisipkan field).

### Sheet "KPI Harga Terakhir" (stat tile)
1. Buat calculated field (*Analysis → Create Calculated Field*):
   - `Minggu Terakhir` = `{ FIXED [commodity_name], [province_name] : MAX([week]) }`
   - `Harga Terakhir` = `IF [week] = [Minggu Terakhir] THEN [avg_price_idr] END`
   - `Harga Setahun Lalu` = `IF [week] = DATEADD('week', -52, [Minggu Terakhir]) THEN [avg_price_idr] END`
   - `Perubahan YoY` = `SUM([Harga Terakhir]) / SUM([Harga Setahun Lalu]) - 1`
2. Seret `Harga Terakhir` (Average) ke **Text**. Mark type: *Text*. Perbesar font.
3. Duplikat sheet untuk `Perubahan YoY` (format persen, 1 desimal).
4. Gunakan filter yang sama dengan "Tren Harga" (klik kanan filter → *Apply to Worksheets →
   All Using This Data Source*).

### Susun dashboard
*Dashboard → New Dashboard* → ukuran **Automatic** → letakkan filter di **satu baris di atas**,
dua KPI di kiri atas, "Tren Harga" di bawahnya. Tambahkan *Text* kecil di bawah:
`Sumber: PIHPS Nasional, Bank Indonesia; Badan Pusat Statistik`.

---

## Dashboard 2 — Efek Lebaran

**Sumber:** `lebaran_index.csv` dan `lebaran_summary.csv`

### Sheet "Indeks Harga Sekitar Lebaran"
1. Seret `t` ke **Columns** → klik kanan → **Dimension** + **Continuous**.
2. Seret `price_index` ke **Rows** → **Average**.
3. Seret `lebaran_year` ke **Detail** (satu garis per tahun).
4. Buat calculated field `Sorotan` =
   `IF [lebaran_year] = {MAX([lebaran_year])} THEN STR([lebaran_year]) ELSE "Tahun lain" END`
   → seret ke **Color** → "Tahun lain" = abu `#c3c2b7`, tahun terakhir = biru `#2a78d6`.
5. Filter `commodity_name` → Single Value (dropdown).
6. *Analytics* pane → seret **Reference Line** ke sumbu `t` → nilai konstan `0`, label
   `Idul Fitri`. Tambah reference line di sumbu Y konstan `1` (= harga normal).
7. Label sumbu X: `Hari relatif terhadap Idul Fitri (negatif = sebelum)`; sumbu Y:
   `Indeks harga (H-60 s.d. H-46 = 1,0)`.

### Sheet "Kenaikan Puncak per Komoditas"
1. Sumber `lebaran_summary.csv`. `median_peak_pct` → **Columns** (Average), `commodity_name`
   → **Rows**, urutkan descending.
2. Warna satu saja: biru `#2a78d6`. Format angka: persen 0 desimal.
3. Seret `peak_week`, `start_rise_week`, dan `recover_week` ke **Tooltip** dan ubah teksnya:
   `Mulai naik minggu ke <start_rise_week>, puncak minggu ke <peak_week>, normal lagi minggu
   ke <recover_week> (minggu -1 = 7 hari terakhir sebelum Lebaran)`.

Susun: bar di kiri, garis di kanan; filter `commodity_name` dipakai untuk garis.

---

## Dashboard 3 — Peta Disparitas Harga

**Sumber:** `province_index.csv` dan `disparity_trend.csv`

### Sheet "Peta"
1. Klik kanan `lat` → *Geographic Role* → **Latitude**; `lon` → **Longitude**.
2. Seret `lon` ke **Columns**, `lat` ke **Rows** (pastikan **Dimension**, bukan SUM).
3. Seret `province_name` ke **Detail**. Mark type: **Circle**.
4. Filter `commodity_name` (single value) dan `month` → *Relative date* → **Last 12 months**.
5. Seret `index_vs_median` (Average) ke **Color** → *Edit Colors* → palet **Red-Blue Diverging**,
   centang *Reversed* bila perlu supaya **merah = lebih mahal**, *Advanced* → **Center = 1**.
6. Size: sedang, sama untuk semua titik.
7. Tooltip: `<province_name>: harga <AVG(index_vs_median)> × median provinsi`.

### Sheet "Per Wilayah Waktu"
`tz_region` → **Rows**, `index_vs_median` (Average) → **Columns**, satu warna biru,
reference line konstan `1`.

### Sheet "Tren Disparitas"
Sumber `disparity_trend.csv`: `month` → **Columns** (continuous month), `cv` (Average) →
**Rows**, filter `commodity_name`. Judul: `Ketimpangan antar provinsi (koefisien variasi)`.

---

## Dashboard 4 — Rantai Pasok & Keterjangkauan

**Sumber:** `supply_chain_markup.csv` dan `affordability.csv`

### Sheet "Markup Rantai Pasok"
1. Buat calculated field `Langkah` = `[from_level] + " → " + [to_level]`.
2. `commodity_name` → **Rows**, `markup_pct` (Average) → **Columns**.
3. `Langkah` → **Color**; urutkan `Langkah` berdasarkan `from_order` (klik kanan → *Sort* →
   *Field* → `from_order` Minimum). Warna: biru, oranye, aqua (urutan rantai).
4. Filter `month` → tahun terakhir.

### Sheet "Keterjangkauan"
1. Sumber `affordability.csv`. `province_name` → **Rows**, `share_of_ump` (Average) →
   **Columns**, urutkan descending, warna biru.
2. Filter `year` → tahun terbaru. Format persen 0 desimal.
3. Judul: `Biaya sembako bulanan (rumah tangga 4 orang) sebagai % UMP`.

---

## Publikasi & ambil link

1. *File → Save to Tableau Public As…* → beri nama `Harga Pangan Indonesia 2018–2026`.
2. Setelah terbuka di browser: tombol **Share** → salin link.
3. Di profil Tableau Public, set workbook ini sebagai **Featured**.
4. Kirim link-nya ke Claude → link dimasukkan ke README (`TABLEAU_PUBLIC_URL`).

## Checklist sebelum publish

- [ ] Setiap dashboard punya teks sumber: *PIHPS Nasional, Bank Indonesia; BPS*.
- [ ] Semua sumbu berlabel, angka rupiah pakai `Rp`, persen pakai `%`.
- [ ] Maksimal 3 warna kategori per chart; garis pembanding abu-abu.
- [ ] Filter ada di satu baris di atas chart yang dipengaruhinya.
- [ ] Judul tiap dashboard berupa **temuan**, bukan sekadar nama data
      (mis. "Cabai naik ±X% menjelang Lebaran", angka dari `lebaran_summary.csv`).
