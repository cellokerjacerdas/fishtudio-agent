# Agent konten harian Fishtudio + Goldfish and Richman

Jalan di GitHub Actions (repo privat `fishtudio-agent`), tidak butuh laptop menyala.

| Jam WIB | Tugas |
|---|---|
| 04.00 | Ambil naskah hari berikutnya dari bank naskah, render 4 video, diunggah ke Drive. Lalu folder buatan agent yang lebih dari 7 hari dipindah ke Sampah Drive. |
| 09.45 | Story STORE OPEN di Goldfish and Richman (render baru tiap hari, tayang tepat 10.00) |
| 11.45 | Posting slot 12.00 (menunggu sampai tepat 12.00) |
| 18.45 | Posting slot 19.00 |

Per akun per hari: **12.00 edukasi** motion graphic (`render/edukasi.cjs`, mesin edu.js) dan **19.00 footage** dari Stock Footage Drive (`render/footage.py`).

Folder Drive: `Fish Studio/[02] CONTENT/<Bulan YY>/<Fishtudio|Goldfish and Richman>/[d m HH.MM] judul/` berisi video, `caption.txt`, `kredit musik.txt`, `dibuat agent.txt`. Setelah tayang muncul `sudah tayang.txt` berisi link.

- Konten di Drive dianggap sudah disetujui. Mau ganti: edit/ganti video atau `caption.txt` sebelum jam tayang. Mau batal: hapus foldernya atau taruh file `sudah tayang.txt`.
- Konten manual tetap bisa: buat folder `[d m 12.00] judul` atau `[d m 19.00] judul` berisi 1 mp4 + caption.txt. Folder tanpa jam dianggap 19.00. Agent hanya membuat konten untuk slot yang masih kosong.
- Yang dihapus otomatis hanya folder yang berisi `dibuat agent.txt`.
- Judul yang sudah dipakai tersimpan di `data/riwayat.json` supaya tidak berulang.

## Gratis: bank naskah

Naskah ditulis di muka (`data/bank.json`, satu entri = 4 konten satu hari) lewat chat dengan Mbut, dicek `setup/cek_bank.py`. Posisi pemakaian di `data/bank_pos.json`. Kalau sisa 5 hari atau kurang, ringkasan run GitHub memberi peringatan: minta Mbut "isi bank naskah". Claude API (`agent/rencana.py`) hanya cadangan kalau bank habis dan secret `ANTHROPIC_API_KEY` diisi (berbayar, saat ini tidak dipakai).

## Rahasia (GitHub > Settings > Secrets > Actions)

`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN`, `IG_TOKEN`, `IG_ID_FISHTUDIO`, `IG_ID_GOLDFISH`. Diisi lewat `setup/google login.bat` (dijalankan di laptop, sekali saja).

## Jalankan manual

GitHub > Actions > agent konten harian > Run workflow, isi `buat`, `posting 12.00`, `posting 19.00`, atau `bersih`.
Atau: `gh workflow run agent.yml -f tugas=buat`.
