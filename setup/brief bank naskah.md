# Brief bank naskah

Aturan isi: konstanta `ATURAN` di `agent/rencana.py` (baca dulu, ikuti semuanya). Contoh gaya caption yang sudah disetujui ada di bawah.

## Format file

File JSON berisi **array 10 hari**. Tiap hari:

```json
{
  "fishtudio": {"edukasi": EDUKASI, "footage": FOOTAGE},
  "goldfish":  {"edukasi": EDUKASI, "footage": FOOTAGE}
}
```

EDUKASI:
```json
{
  "judul": "ganti air jangan dikuras",
  "klip": "akuarium ranchu",
  "adegan": [
    {"vo": "Ganti air akuarium, jangan dikuras semua.", "headline": "Ganti air [jangan dikuras] semua.",
     "visual": {"jenis": "salah", "angka": "", "satuan": "", "label": "", "poin": []}},
    {"vo": "Cukup tiga puluh persen, seminggu sekali.", "headline": "Cukup [30%] seminggu sekali.",
     "visual": {"jenis": "angka", "angka": "30", "satuan": "%", "label": "air per minggu", "poin": []}},
    {"vo": "Bakteri baik di filter tetap hidup, ikan nggak kaget.", "headline": "Bakteri baik [tetap hidup].",
     "visual": {"jenis": "daftar", "angka": "", "satuan": "", "label": "", "poin": ["Filter aman", "Air stabil", "Ikan tenang"]}}
  ],
  "cta_vo": "Hubungi Fishtudio untuk perawatan akuariummu.",
  "cta_teks": "Hubungi [Fishtudio] sekarang",
  "caption": "Ganti air jangan dikuras habis. Chat WA 08569990738, kirim kata RAWAT untuk jadwal perawatan akuarium.\n\nParagraf 2.\n\nParagraf 3.",
  "tagar_topik": "perawatanakuarium"
}
```

FOOTAGE:
```json
{
  "judul": "oranda pilihan minggu ini",
  "kategori": "oranda",
  "adegan": [
    {"vo": "Oranda dengan wen tebal, siap pindah ke akuariummu.", "teks": "Oranda wen tebal"},
    {"vo": "...", "teks": "..."},
    {"vo": "...", "teks": "..."}
  ],
  "cta_vo": "Pesan oranda di Goldfish and Richman sekarang.",
  "cta_teks": "Chat WA 0856 9990 738",
  "caption": "...",
  "tagar_topik": "oranda"
}
```

## Batas yang dicek otomatis (`python -X utf8 setup/cek_bank.py <file>`)

- Edukasi 3 atau 4 adegan, footage tepat 3 adegan.
- `vo` maks 12 kata. `headline` maks 6 kata dan wajib ada `[frasa kunci]`. `teks` footage maks 7 kata. `cta_teks` maks 6 kata. `cta_vo` maks 12 kata.
- Visual `angka`: isi `angka` (angka saja, contoh "30", "2", "24") + `satuan` pendek ("%", "x", "") + `label` maks 4 kata. Visual `daftar`: 2 sampai 3 `poin`, tiap poin maks 3 kata. Kolom yang tidak dipakai diisi "" atau [].
- `klip` salah satu dari `KLIP_LATAR`, `kategori` dari `KATEGORI[brand]` (lihat rencana.py).
- `judul` huruf kecil, angka, spasi saja, maks 7 kata, tidak boleh sama dengan judul lain.
- Caption: baris pertama maks 120 karakter, berisi `08569990738` dan satu KATA KUNCI huruf besar (RAWAT, ORANDA, PAKAN, dll). Lalu 2 sampai 3 paragraf pendek dipisah baris kosong. Tanpa hashtag, link, emoji, tanda pisah. Total maks 1200 karakter. Jangan tulis tagline, kredit musik, atau hashtag (ditambah sistem).
- `tagar_topik` huruf kecil tanpa spasi (wajib isi untuk Fishtudio; untuk Goldfish boleh isi tapi tidak dipakai).
- Kata terlarang: si jambul (pakai "wen"), Molly Feeds, Koi Feeds, ternak sendiri, sortiran, protein angka, delapan tahun, ekspor, harga ikan. Harga yang boleh hanya Gold Feeds Rp43 ribu per 300 g.

## Narasi Threads (field `threads`, sejak 21 Nov 2026)

Tiap konten (edukasi dan footage) diberi field `threads`: versi Threads dari konten yang sama, ditulis jadi `threads.txt` dan diposting bersama video. FB memakai caption IG apa adanya; Threads tidak.

- Lebih panjang dan manusiawi dari caption: 500 sampai 1400 karakter, 3 sampai 5 paragraf, tiap paragraf maks 480 karakter (Threads membatasi 500 karakter per post; paragraf lanjutan jadi balasan berantai).
- Suara orang toko yang cerita, bukan iklan. Buka dengan kejadian yang umum (pelanggan yang tanya, kesalahan yang sering dilihat tim, momen di toko), baru masuk ke tipsnya. Boleh "kami", "kamu", "nggak".
- Tanpa daftar bernomor, tanpa hashtag, tanpa emoji, tanpa tanda pisah, tanpa link.
- Satu ajakan di paragraf terakhir: tanya balik ke pembaca (biar ada balasan) atau WA 08569990738. Tanpa tagline dan kredit musik.
- Kata terlarang dan aturan fakta sama dengan caption.

## Variasi

- Jenis visual edukasi divariasikan antar hari; jangan semua adegan "akuarium".
- Footage Fishtudio cuma dua kategori ("kasih makan" = momen ikan makan Gold Feeds, "perawatan akuarium" = tim merawat akuarium klien). Bedakan sudutnya lewat teks dan VO.
- Footage Goldfish bergiliran oranda, ryukin, ranchu, panda tanco, mas koki campur.
- VO kalimat lisan yang enak didengar, sopan, sedikit santai ("nggak" boleh). Fakta harus benar dan umum dipakai penghobi; kalau ragu, jangan tulis angka.
- Kata kunci WA beragam per konten (RAWAT, FILTER, PAKAN, GROOMING, ORANDA, RYUKIN, RANCHU, KOKI, CEK, dll).
