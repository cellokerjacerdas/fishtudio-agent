"""Buat konten dari bank naskah di laptop, langsung ke Drive lewat G: (cadangan sebelum/tanpa GitHub).

python -X utf8 setup/buat_lokal.py <d> <m> <jumlah hari> [--slot 12.00|19.00|12.00,19.00]
Contoh: buat_lokal.py 20 11 5   -> 20 sampai 24 Nov, slot yang masih kosong saja.
Naskah dipilih per slot dari data/bank.json berdasarkan data/evaluasi.json (hasil checker 05.00):
tema yang terbukti kuat didahulukan, tema lemah ditahan. Tanpa evaluasi, urutan bank dipakai.
Naskah terpakai dicatat per brand:jenis di data/bank_pos.json.
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
sys.path.insert(0, str(REPO / "render"))
import main as M  # noqa: E402
import tema as T  # noqa: E402
import thumbnail as THUMB  # noqa: E402

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
        p = AKAR / "[00] Other" / "Stock Footage" / sub
        if p.exists():
            calon += [f for f in p.iterdir() if f.suffix.lower() in (".mp4", ".mov")]
    for f in random.sample(calon, min(jumlah, len(calon))):
        shutil.copy(f, dest / f.name)
    return dest


AJAKAN_KOMENTAR = {  # dipasang kalau checker menemukan komentar sepi
    "fishtudio": "Akuariummu pernah ngalamin ini? Cerita di komentar, tim Fishtudio bantu jawab.",
    "goldfish": "Mas koki kamu pernah begini? Cerita di komentar, nanti kami bantu jawab.",
}


def muat_terpakai(bank, riwayat, pos_data):
    """Naskah yang sudah dipakai per brand:jenis. Data lama cuma punya posisi hari, jadi diisi dari sana + riwayat."""
    if "terpakai" in pos_data:
        return {k: set(v) for k, v in pos_data["terpakai"].items()}
    awal = pos_data.get("berikutnya", 0)
    terpakai = {f"{b}:{j}": set(range(awal)) for b in M.FOLDER for j in M.SLOT}
    idx = T.indeks_judul(bank)
    for r in riwayat:
        hit = idx.get(T.norm(r.get("judul")))
        if hit:
            terpakai[f"{hit[1]}:{hit[2]}"].add(hit[0])
    return terpakai


def simpan_terpakai(bank, terpakai):
    # "berikutnya" tetap ditulis untuk agent cloud (main.py), = hari pertama yang masih punya naskah kosong
    sisa = [i for i in range(len(bank)) if any(i not in v for v in terpakai.values())]
    M.POS.write_text(json.dumps({"berikutnya": sisa[0] if sisa else len(bank),
                                 "terpakai": {k: sorted(v) for k, v in terpakai.items()}}), encoding="utf-8")


def sisa_bank():
    bank = json.loads(M.BANK.read_text(encoding="utf-8"))
    pos_data = T.baca(M.POS, {})
    riwayat = T.baca(M.RIWAYAT, [])
    terpakai = muat_terpakai(bank, riwayat, pos_data)
    return min(len(bank) - len(v) for v in terpakai.values())


def evaluasi_segar():
    """Hasil checker pagi; dipakai kalau umurnya paling lama 2 hari."""
    ev = T.baca(T.EVALUASI, {})
    try:
        if dt.date.today() - dt.date.fromisoformat(ev["tanggal"]) <= dt.timedelta(days=2):
            return ev
    except (KeyError, ValueError):
        pass
    return {}


def pilih_naskah(bank, brand, jenis, terpakai, riwayat, ev):
    """Naskah yang jadi solusi evaluasi: tema yang skornya tinggi didahulukan, tema lemah ditahan,
    tema yang baru tayang 2 kali terakhir diberi jeda supaya feed tidak monoton."""
    skor_tema = ((ev.get("akun") or {}).get(brand) or {}).get("tema", {}).get(jenis, {})
    baru = [r.get("tema") or T.tema_riwayat(r, bank) for r in riwayat
            if r.get("brand") == brand and r.get("slot") == M.SLOT[jenis]][-2:]
    calon = []
    for i, hari in enumerate(bank):
        item = (hari.get(brand) or {}).get(jenis)
        if not item or i in terpakai[f"{brand}:{jenis}"]:
            continue
        t = T.tema(brand, jenis, item)
        s = skor_tema.get(t)
        nilai = (s["jumlah"] * s["skor"] + 2) / (s["jumlah"] + 2) if s else 1.0  # data sedikit ditarik ke rata rata
        if t in baru:
            nilai *= 0.85
        calon.append((-nilai, i, t, item))
    if not calon:
        return None, None, None
    _, i, t, item = min(calon, key=lambda c: (c[0], c[1]))
    return i, t, item


def main():
    args = sys.argv[1:]
    hanya = set(args[args.index("--slot") + 1].split(",")) if "--slot" in args else None
    hari_ini = dt.date.today()
    d0 = dt.date(hari_ini.year, int(args[1]), int(args[0]))
    if d0 < hari_ini - dt.timedelta(days=60):  # 1 Januari diminta saat masih Desember
        d0 = d0.replace(year=d0.year + 1)
    hari = int(args[2])
    bank = json.loads(M.BANK.read_text(encoding="utf-8"))
    pos_data = T.baca(M.POS, {})
    riwayat = json.loads(M.RIWAYAT.read_text(encoding="utf-8")) if M.RIWAYAT.exists() else []
    terpakai = muat_terpakai(bank, riwayat, pos_data)
    ev = evaluasi_segar()
    print(f"evaluasi checker: {ev.get('tanggal', 'tidak ada, pakai urutan bank')}")
    TMP.mkdir(exist_ok=True)
    for k in range(hari):
        d = d0 + dt.timedelta(days=k)
        for brand in M.FOLDER:
            fb = AKAR / M.nama_bulan(d) / M.FOLDER[brand]
            for jenis, slot in M.SLOT.items():
                if (hanya and slot not in hanya) or slot_terisi(fb, d, slot):
                    continue
                i, tema, item = pilih_naskah(bank, brand, jenis, terpakai, riwayat, ev)
                if item is None:
                    print(f"BANK NASKAH HABIS untuk {brand} {jenis}: minta Mbut isi bank naskah")
                    continue
                if ((ev.get("akun") or {}).get(brand) or {}).get("komentar_rendah"):
                    item = dict(item, caption=item["caption"].rstrip() + "\n\n" + AJAKAN_KOMENTAR[brand])
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
                    sumber_thumb = THUMB.sumber_edukasi(item, REPO)
                else:
                    klip = klip_lokal(item["kategori"], TMP / "klip")
                    sumber_thumb = next(iter(sorted(klip.iterdir())), None)
                    subprocess.run([sys.executable, "-X", "utf8", str(REPO / "render/footage.py"), str(spec), brand,
                                    str(klip), str(TMP / "kerja"), str(video)], check=True)
                tujuan = fb / f"[{d.day} {d.month} {slot}] {judul}"
                tujuan.mkdir(parents=True, exist_ok=True)
                shutil.move(str(video), tujuan / f"{judul}.mp4")
                try:  # thumbnail otomatis, jadi cover Reels saat posting (permintaan Cello 21 Nov 2026)
                    THUMB.buat(item, brand, jenis, sumber_thumb, tujuan / M.NAMA_THUMB)
                except Exception as e:  # noqa: BLE001  thumbnail gagal jangan batalkan konten
                    print(f"PERINGATAN thumbnail {tujuan.name}: {e}")
                (tujuan / "caption.txt").write_text(caption, encoding="utf-8")
                if item.get("threads"):  # narasi Threads, lebih panjang dari caption (Cello 21 Nov 2026)
                    (tujuan / "threads.txt").write_text(item["threads"].strip() + "\n", encoding="utf-8")
                (tujuan / "kredit musik.txt").write_text(M.kredit(musik) + "\n", encoding="utf-8")
                (tujuan / M.TANDA_AGENT).write_text(
                    f"dibuat {dt.datetime.now():%d/%m/%Y %H:%M} WIB, dihapus otomatis setelah 7 hari\n", encoding="utf-8")
                riwayat.append({"tanggal": d.isoformat(), "brand": brand, "slot": slot, "judul": judul,
                                "tema": tema, "bank": i})
                terpakai[f"{brand}:{jenis}"].add(i)
                simpan_terpakai(bank, terpakai)
                M.RIWAYAT.write_text(json.dumps(riwayat, ensure_ascii=False, indent=1), encoding="utf-8")
                print(f"SIAP {tujuan} (tema {tema}, naskah hari {i + 1})", flush=True)
    simpan_terpakai(bank, terpakai)
    shutil.rmtree(TMP / "kerja", ignore_errors=True)
    shutil.rmtree(TMP / "klip", ignore_errors=True)
    print(f"selesai, sisa naskah paling sedikit {min(len(bank) - len(v) for v in terpakai.values())}")


if __name__ == "__main__":
    main()
