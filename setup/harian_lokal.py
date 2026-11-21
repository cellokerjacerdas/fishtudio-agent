"""Agent harian versi laptop: bikin konten ke Drive, lalu bersihkan video lama. Dipanggil Task Scheduler
"Fishtudio agent harian" (05.00, jalan begitu laptop menyala kalau jamnya terlewat).

python -X utf8 setup/harian_lokal.py            buat + bersih
python -X utf8 setup/harian_lokal.py bersih     bersih saja
python -X utf8 setup/harian_lokal.py cek        tampilkan yang akan dihapus, tanpa menghapus

Buat: slot hari ini yang belum lewat dan semua slot besok yang masih kosong (naskah dari bank naskah).
Bersih: semua video di [02] CONTENT/<Bulan YY>/ yang sudah 7 hari di Drive dan jadwal tayangnya sudah lewat.
  - Kalau env GOOGLE_CLIENT_ID/SECRET/REFRESH_TOKEN ada: hapus permanen lewat Drive API (sama dengan cloud).
  - Kalau belum: hapus lewat G:, Google Drive for desktop memindahnya ke Sampah Drive (kuota lega setelah
    Sampah dikosongkan atau 30 hari).
Stock Footage dan folder di luar [02] CONTENT tidak pernah disentuh.
"""
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "agent"))
sys.path.insert(0, str(REPO / "setup"))
import main as M  # noqa: E402
from buat_lokal import AKAR, slot_terisi  # noqa: E402

LOG = REPO / "_tmp" / "log harian.txt"


def log(teks):
    baris = f"[{dt.datetime.now():%d/%m %H:%M}] {teks}"
    print(baris, flush=True)
    LOG.parent.mkdir(exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(baris + "\n")


def buat():
    kini = dt.datetime.now()
    for d in (kini.date(), kini.date() + dt.timedelta(days=1)):
        slot = []
        for jenis, s in M.SLOT.items():
            jam, menit = map(int, s.split("."))
            batas = dt.datetime.combine(d, dt.time(jam, menit)) - dt.timedelta(minutes=30)
            kosong = any(not slot_terisi(AKAR / M.nama_bulan(d) / M.FOLDER[b], d, s) for b in M.FOLDER)
            if kosong and kini < batas:
                slot.append(s)
        if not slot:
            continue
        log(f"buat {d:%d/%m} slot {','.join(slot)}")
        r = subprocess.run([sys.executable, "-X", "utf8", str(REPO / "setup/buat_lokal.py"), str(d.day), str(d.month),
                            "1", "--slot", ",".join(slot)], capture_output=True, text=True, encoding="utf-8")
        for baris in (r.stdout + r.stderr).strip().splitlines()[-15:]:
            log("  " + baris)
        if r.returncode:
            log(f"  GAGAL buat {d:%d/%m} (kode {r.returncode})")
    bank = json.loads(M.BANK.read_text(encoding="utf-8"))
    pos = json.loads(M.POS.read_text(encoding="utf-8")).get("berikutnya", 0)
    if len(bank) - pos <= 5:
        log(f"PERINGATAN: bank naskah sisa {len(bank) - pos} hari, minta Mbut isi bank naskah")


def bersih_g(cek):
    kini = dt.datetime.now(M.WIB)
    total, n = 0, 0
    for bulan in AKAR.iterdir():
        m = M.POLA_BULAN.match(bulan.name)
        if not (bulan.is_dir() and m):
            continue
        tahun = 2000 + int(m[2])
        for f in bulan.rglob("*"):
            if not f.is_file():
                continue
            tgl = None
            for induk in reversed(f.relative_to(bulan).parents):
                tgl = M.tanggal_folder(induk.name, tahun, tgl)
            dibuat = dt.datetime.fromtimestamp(f.stat().st_ctime, M.WIB)
            if M.boleh_hapus(f.name, "", dibuat, tgl, kini):
                ukuran = f.stat().st_size
                if not cek:
                    try:
                        f.unlink()
                    except OSError as e:
                        log(f"LEWAT (dicoba lagi besok): {f.relative_to(AKAR)}: {e.strerror}")
                        continue
                total, n = total + ukuran, n + 1
                log(f"{'AKAN DIHAPUS' if cek else 'DIHAPUS ke Sampah Drive'}: {f.relative_to(AKAR)}")
    log(f"bersih{' (cek)' if cek else ''}: {n} video, {total / 1e6:.0f} MB")


def bersih(cek=False):
    if not cek and all(os.environ.get(k) for k in ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REFRESH_TOKEN")):
        M.cmd_bersih(None)
        for baris in M.laporan:
            log(baris)
    else:
        bersih_g(cek)


if __name__ == "__main__":
    tugas = sys.argv[1] if len(sys.argv) > 1 else "semua"
    try:
        if tugas == "semua":
            buat()
        bersih(cek=tugas == "cek")
    except Exception as e:  # noqa: BLE001
        log(f"ERROR {type(e).__name__}: {e}")
        raise
