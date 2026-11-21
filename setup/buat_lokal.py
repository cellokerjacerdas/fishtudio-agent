"""Buat konten dari bank naskah di laptop, langsung ke Drive lewat G: (cadangan sebelum/tanpa GitHub).

python -X utf8 setup/buat_lokal.py <d> <m> <jumlah hari> [--slot 12.00|19.00|12.00,19.00]
Contoh: buat_lokal.py 20 11 5   -> 20 sampai 24 Nov, slot yang masih kosong saja.
Naskah diambil dari data/bank.json mulai posisi data/bank_pos.json, posisi maju satu per hari yang benar-benar dibuat.
"""
import datetime as dt
import json
import random
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "agent"))
import main as M  # noqa: E402

AKAR = Path(r"G:\My Drive\Fish Studio\[02] CONTENT")
TMP = REPO / "_tmp"


def slot_terisi(folder_brand, d, slot):
    if not folder_brand.exists():
        return False
    for f in folder_brand.iterdir():
        m = M.POLA.match(f.name)
        if f.is_dir() and m and int(m[1]) == d.day and int(m[2]) == d.month and (m[3] or "19.00") == slot:
            return True
    return False


def klip_lokal(kategori, dest, jumlah=4):
    shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir(parents=True, exist_ok=True)  # Windows kadang belum melepas folder lama
    for sisa in dest.iterdir():
        sisa.unlink(missing_ok=True)
    calon = []
    for sub in M.SUMBER_FOOTAGE[kategori]:
        p = AKAR / "Stock Footage" / sub
        if p.exists():
            calon += [f for f in p.iterdir() if f.suffix.lower() in (".mp4", ".mov")]
    for f in random.sample(calon, min(jumlah, len(calon))):
        shutil.copy(f, dest / f.name)
    return dest


def main():
    args = sys.argv[1:]
    hanya = set(args[args.index("--slot") + 1].split(",")) if "--slot" in args else None
    hari_ini = dt.date.today()
    d0 = dt.date(hari_ini.year, int(args[1]), int(args[0]))
    if d0 < hari_ini - dt.timedelta(days=60):  # 1 Januari diminta saat masih Desember
        d0 = d0.replace(year=d0.year + 1)
    hari = int(args[2])
    bank = json.loads(M.BANK.read_text(encoding="utf-8"))
    pos = json.loads(M.POS.read_text(encoding="utf-8")).get("berikutnya", 0) if M.POS.exists() else 0
    riwayat = json.loads(M.RIWAYAT.read_text(encoding="utf-8")) if M.RIWAYAT.exists() else []
    TMP.mkdir(exist_ok=True)
    for k in range(hari):
        d = d0 + dt.timedelta(days=k)
        if pos >= len(bank):
            print("BANK NASKAH HABIS: minta Mbut isi bank naskah")
            break
        naskah = bank[pos]
        dibuat = 0
        for brand in M.FOLDER:
            fb = AKAR / M.nama_bulan(d) / M.FOLDER[brand]
            for jenis, slot in M.SLOT.items():
                if (hanya and slot not in hanya) or slot_terisi(fb, d, slot):
                    continue
                item = naskah[brand][jenis]
                musik = random.choice(M.MUSIK[brand])
                judul = re.sub(r"[^a-z0-9 ]", "", item["judul"].lower()).strip()
                caption = M.susun_caption(brand, item, musik)
                cap = TMP / M.FOLDER[brand] / "caption.txt"  # cek.js menebak brand dari path
                cap.parent.mkdir(exist_ok=True)
                cap.write_text(caption, encoding="utf-8")
                ok, out = M.cek_copy(cap)
                if not ok:
                    print(f"LEWAT {d:%d/%m} {brand} {slot} {judul}: cek copy\n{out}")
                    continue
                spec = TMP / f"{brand}-{jenis}.json"
                spec.write_text(json.dumps(dict(item, musik=musik), ensure_ascii=False), encoding="utf-8")
                video = TMP / f"{judul}.mp4"
                if jenis == "edukasi":
                    subprocess.run(["node", str(REPO / "render/edukasi.cjs"), str(spec), brand,
                                    str(TMP / "kerja"), str(video)], check=True, shell=False)
                else:
                    klip = klip_lokal(item["kategori"], TMP / "klip")
                    subprocess.run([sys.executable, "-X", "utf8", str(REPO / "render/footage.py"), str(spec), brand,
                                    str(klip), str(TMP / "kerja"), str(video)], check=True)
                tujuan = fb / f"[{d.day} {d.month} {slot}] {judul}"
                tujuan.mkdir(parents=True, exist_ok=True)
                shutil.move(str(video), tujuan / f"{judul}.mp4")
                (tujuan / "caption.txt").write_text(caption, encoding="utf-8")
                (tujuan / "kredit musik.txt").write_text(M.kredit(musik) + "\n", encoding="utf-8")
                (tujuan / M.TANDA_AGENT).write_text(
                    f"dibuat {dt.datetime.now():%d/%m/%Y %H:%M} WIB, dihapus otomatis setelah 7 hari\n", encoding="utf-8")
                riwayat.append({"tanggal": d.isoformat(), "brand": brand, "slot": slot, "judul": judul})
                dibuat += 1
                print(f"SIAP {tujuan}", flush=True)
        pos += 1 if dibuat else 0
        M.POS.write_text(json.dumps({"berikutnya": pos}), encoding="utf-8")
        M.RIWAYAT.write_text(json.dumps(riwayat, ensure_ascii=False, indent=1), encoding="utf-8")
    shutil.rmtree(TMP / "kerja", ignore_errors=True)
    shutil.rmtree(TMP / "klip", ignore_errors=True)
    print(f"selesai, posisi bank sekarang {pos}")


if __name__ == "__main__":
    main()
