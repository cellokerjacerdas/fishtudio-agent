# Agent konten harian Fishtudio + Goldfish and Richman

Jalan di GitHub Actions (repo privat `fishtudio-agent`), tidak butuh laptop menyala.

| Jam WIB | Tugas |
|---|---|
| 04.00 | Claude menulis 4 naskah, video dirender, diunggah ke Drive. Lalu folder buatan agent yang lebih dari 7 hari dipindah ke Sampah Drive. |
| 11.45 | Posting slot 12.00 (menunggu sampai tepat 12.00) |
| 18.45 | Posting slot 19.00 |

Per akun per hari: **12.00 edukasi** motion graphic (`render/edukasi.cjs`, mesin edu.js) dan **19.00 footage** dari Stock Footage Drive (`render/footage.py`).

Folder Drive: `Fish Studio/[02] CONTENT/<Bulan YY>/<Fishtudio|Goldfish and Richman>/[d m HH.MM] judul/` berisi video, `caption.txt`, `kredit musik.txt`, `dibuat agent.txt`. Setelah tayang muncul `sudah tayang.txt` berisi link.

- Konten di Drive dianggap sudah disetujui. Mau ganti: edit/ganti video atau `caption.txt` sebelum jam tayang. Mau batal: hapus foldernya atau taruh file `sudah tayang.txt`.
- Konten manual tetap bisa: buat folder `[d m 12.00] judul` atau `[d m 19.00] judul` berisi 1 mp4 + caption.txt. Folder tanpa jam dianggap 19.00. Agent hanya membuat konten untuk slot yang masih kosong.
- Yang dihapus otomatis hanya folder yang berisi `dibuat agent.txt`.
- Judul yang sudah dipakai tersimpan di `data/riwayat.json` supaya tidak berulang.

## Rahasia (GitHub > Settings > Secrets > Actions)

`ANTHROPIC_API_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN`, `IG_TOKEN`, `IG_ID_FISHTUDIO`, `IG_ID_GOLDFISH`. Diisi lewat `setup/pasang rahasia.bat` dan `setup/google login.bat` (dijalankan di laptop, sekali saja).

## Jalankan manual

GitHub > Actions > agent konten harian > Run workflow, isi `buat`, `posting 12.00`, `posting 19.00`, atau `bersih`.
Atau: `gh workflow run agent.yml -f tugas=buat`.
