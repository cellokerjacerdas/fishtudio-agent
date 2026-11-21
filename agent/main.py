"""Agent konten harian Fishtudio + Goldfish and Richman (jalan di GitHub Actions).

python agent/main.py buat [d m]        04.00 WIB: tulis, render, unggah 4 video ke Drive
python agent/main.py posting 12.00     posting slot 12.00 (atau 19.00) ke Instagram
python agent/main.py bersih            buang folder buatan agent yang lebih dari 7 hari
python agent/main.py story             10.00 WIB: story STORE OPEN di Goldfish and Richman

Struktur Drive: Fish Studio/[02] CONTENT/<Bulan YY>/<Fishtudio|Goldfish and Richman>/[d m HH.MM] judul/
Folder lama tanpa jam ([d m] judul) dianggap slot 19.00.
"""
import datetime as dt
import json
import os
import random
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
import fb  # noqa: E402
import gdrive  # noqa: E402
from rencana import buat_rencana  # noqa: E402  (cadangan berbayar, hanya kalau bank habis)

REPO = Path(__file__).resolve().parent.parent
TMP = Path(os.environ.get("RUNNER_TEMP", REPO / "_tmp")) / "agent"
WIB = dt.timezone(dt.timedelta(hours=7))
BULAN = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober",
         "November", "Desember"]
FOLDER = {"fishtudio": "Fishtudio", "goldfish": "Goldfish and Richman"}
HASHTAG = {"fishtudio": "#Fishtudio #Aquariummalang #Perawatanaquariumindonesia #Aquascape",
           "goldfish": "#goldfishindonesia #goldfishmalang #maskokiindonesia #maskokimalang #goldfishandrichman"}
TAGLINE = {"fishtudio": "Fishtudio. Luxury living, inspired by nature.",
           "goldfish": "Goldfish & Richman by Fish Studio."}
MUSIK = {"fishtudio": ["fishtudio bossa antigua.mp3", "fishtudio lobby time.mp3", "fishtudio vibing over venus.mp3"],
         "goldfish": ["goldfish carefree.mp3", "goldfish easy lemon.mp3", "goldfish wallpaper.mp3"]}
SUMBER_FOOTAGE = {
    "oranda": ["VIDEO IKAN/ORANDA", "VIDEO IKAN/ORANDA/Satuan SQ"],
    "ryukin": ["VIDEO IKAN/RYUKIN"],
    "ranchu": ["VIDEO IKAN/RANCHU/Satuan"],
    "panda tanco": ["VIDEO IKAN/PANDA & TANCO"],
    "mas koki campur": ["VIDEO IKAN/Footage riska"],
    "kasih makan": ["Footage 25 Okt/ngasih makan"],
    "perawatan akuarium": ["Footage Abe 9 Nov"],
}
SLOT = {"edukasi": "12.00", "footage": "19.00"}
TANDA_AGENT, TANDA_TAYANG, TANDA_FB = "dibuat agent.txt", "sudah tayang.txt", "sudah tayang fb.txt"
POLA = re.compile(r"^\[(\d{1,2}) (\d{1,2})(?: (\d{1,2}\.\d{2}))?\]\s*(.*)$")
RIWAYAT = REPO / "data/riwayat.json"
laporan = []


def lapor(teks):
    print(teks, flush=True)
    laporan.append(teks)


def sekarang():
    return dt.datetime.now(WIB)


def nama_bulan(d):
    return f"{BULAN[d.month - 1]} {d:%y}"


def folder_brand(d, brand, buat=False):
    return gdrive.jalur("Fish Studio", "[02] CONTENT", nama_bulan(d), FOLDER[brand], buat=buat)


def folder_slot(d, brand, slot):
    """Folder konten untuk tanggal + slot (folder lama tanpa jam = 19.00)."""
    par = folder_brand(d, brand)
    if not par:
        return []
    hasil = []
    for f in gdrive.daftar(par, True):
        m = POLA.match(f["name"])
        if m and int(m[1]) == d.day and int(m[2]) == d.month and (m[3] or "19.00") == slot:
            hasil.append(f)
    return hasil


def kredit(musik):
    judul = musik.split(" ", 1)[1].rsplit(".", 1)[0].title()
    return f'Music: "{judul}" by Kevin MacLeod (incompetech.com), licensed under CC BY 4.0'


def susun_caption(brand, item, musik):
    tag = HASHTAG[brand]
    topik = re.sub(r"[^a-z0-9]", "", (item.get("tagar_topik") or "").lower())
    if brand == "fishtudio" and topik and f"#{topik}" not in tag.lower():
        tag += f" #{topik}"
    return f"{item['caption'].strip()}\n\n{TAGLINE[brand]}\n\n{kredit(musik)}\n\n{tag}"


def cek_copy(path):
    r = subprocess.run(["node", str(REPO / "agent/cek.js"), str(path)], capture_output=True, text=True, encoding="utf-8")
    return r.returncode == 0, r.stdout


# ---------------- buat ----------------

def unduh_footage(kategori, dest, jumlah=4):
    dest.mkdir(parents=True, exist_ok=True)
    akar = gdrive.jalur("Fish Studio", "[02] CONTENT", "Stock Footage")
    calon = []
    for sub in SUMBER_FOOTAGE[kategori]:
        fid = gdrive.jalur(*sub.split("/"), akar=akar)
        if fid:
            calon += [f for f in gdrive.daftar(fid, False) if f["name"].lower().endswith((".mp4", ".mov"))
                      and int(f.get("size", 0)) < 400 * 1024 * 1024]
    if not calon:
        raise RuntimeError(f"footage kategori {kategori} kosong")
    for f in random.sample(calon, min(jumlah, len(calon))):
        gdrive.unduh(f["id"], dest / f["name"])
    return dest


def render(brand, jenis, item, musik, out):
    spec = dict(item, musik=musik)
    work = TMP / f"{brand}-{jenis}"
    sp = TMP / f"{brand}-{jenis}.json"
    sp.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
    if jenis == "edukasi":
        subprocess.run(["node", str(REPO / "render/edukasi.cjs"), str(sp), brand, str(work), str(out)], check=True)
    else:
        klip = unduh_footage(item["kategori"], TMP / f"klip-{brand}")
        subprocess.run([sys.executable, str(REPO / "render/footage.py"), str(sp), brand, str(klip), str(work), str(out)],
                       check=True)
        shutil.rmtree(klip, ignore_errors=True)
    shutil.rmtree(work, ignore_errors=True)


BANK, POS = REPO / "data/bank.json", REPO / "data/bank_pos.json"


def ambil_naskah(d, riwayat):
    """Naskah gratis dari bank (data/bank.json, satu entri per hari). Claude API hanya cadangan kalau bank habis."""
    bank = json.loads(BANK.read_text(encoding="utf-8")) if BANK.exists() else []
    pos = json.loads(POS.read_text(encoding="utf-8")).get("berikutnya", 0) if POS.exists() else 0
    if pos < len(bank):
        POS.write_text(json.dumps({"berikutnya": pos + 1}), encoding="utf-8")
        sisa = len(bank) - pos - 1
        lapor(f"Naskah bank hari ke-{pos + 1} dari {len(bank)}, sisa {sisa} hari")
        if sisa <= 5:
            lapor(f"PERINGATAN: bank naskah tinggal {sisa} hari. Minta Mbut 'isi bank naskah'.")
        return bank[pos]
    if os.environ.get("ANTHROPIC_API_KEY"):
        return buat_rencana(f"{d.day} {BULAN[d.month - 1]} {d.year}", riwayat)
    raise SystemExit("Bank naskah habis dan tidak ada ANTHROPIC_API_KEY. Minta Mbut 'isi bank naskah'.")


def cmd_buat(argumen):
    d = sekarang().date()
    if len(argumen) >= 2:
        d = d.replace(month=int(argumen[1]), day=int(argumen[0]))
    TMP.mkdir(parents=True, exist_ok=True)
    perlu = [(b, j) for b in FOLDER for j in SLOT if not folder_slot(d, b, SLOT[j])]
    if not perlu:
        lapor(f"{d:%d/%m}: semua slot sudah ada di Drive")
        return
    riwayat = json.loads(RIWAYAT.read_text(encoding="utf-8")) if RIWAYAT.exists() else []
    rencana = ambil_naskah(d, riwayat)
    gagal = 0
    for brand, jenis in perlu:
        item = rencana[brand][jenis]
        slot = SLOT[jenis]
        musik = random.choice(MUSIK[brand])
        judul = re.sub(r"[^a-z0-9 ]", "", item["judul"].lower()).strip() or f"{jenis} {brand}"
        caption = susun_caption(brand, item, musik)
        cap_file = TMP / FOLDER[brand] / "caption.txt"  # cek.js menebak brand dari path
        cap_file.parent.mkdir(parents=True, exist_ok=True)
        cap_file.write_text(caption, encoding="utf-8")
        semua_teks = TMP / "teks layar.txt"
        layar = [a.get("headline") or a.get("teks", "") for a in item["adegan"]]
        semua_teks.write_text("\n".join([a["vo"] for a in item["adegan"]] + layar + [item["cta_vo"], item["cta_teks"]]),
                              encoding="utf-8")
        ok1, out1 = cek_copy(cap_file)
        ok2, out2 = cek_copy(semua_teks)
        if not (ok1 and ok2):
            lapor(f"LEWAT {brand} {slot} '{judul}': gagal cek copy\n{out1}{out2}")
            gagal += 1
            continue
        video = TMP / f"{judul}.mp4"
        try:
            render(brand, jenis, item, musik, video)
        except Exception as e:  # satu konten gagal jangan hentikan yang lain
            lapor(f"GAGAL render {brand} {slot} '{judul}': {e}")
            gagal += 1
            continue
        par = folder_brand(d, brand, buat=True)
        fid = gdrive.buat_folder(par, f"[{d.day} {d.month} {slot}] {judul}")
        gdrive.unggah(video, fid, f"{judul}.mp4", "video/mp4")
        gdrive.tulis_teks(fid, "caption.txt", caption)
        gdrive.tulis_teks(fid, "kredit musik.txt", kredit(musik) + "\n")
        gdrive.tulis_teks(fid, TANDA_AGENT, f"dibuat {sekarang():%d/%m/%Y %H:%M} WIB, dihapus otomatis setelah 7 hari\n")
        video.unlink(missing_ok=True)
        riwayat.append({"tanggal": d.isoformat(), "brand": brand, "slot": slot, "judul": judul})
        lapor(f"SIAP {brand} {slot}: [{d.day} {d.month} {slot}] {judul}")
    RIWAYAT.parent.mkdir(exist_ok=True)
    RIWAYAT.write_text(json.dumps(riwayat, ensure_ascii=False, indent=1), encoding="utf-8")
    if gagal:
        raise SystemExit(f"{gagal} konten gagal dibuat")


# ---------------- posting ----------------

def ig(metode, jalur, token, **kw):
    r = requests.request(metode, f"https://graph.facebook.com/v23.0/{jalur}",
                         params={"access_token": token, **kw.pop("params", {})}, timeout=60, **kw)
    d = r.json()
    if "error" in d:
        raise RuntimeError(d["error"].get("message", d))
    return d


def unggah_coba(*a, **kw):
    """Ulangi sekali dengan wadah baru kalau Meta gagal memproses (ProcessingFailedError, 20 Nov 2026)."""
    for coba in range(3):
        try:
            return unggah_reel(*a, **kw)
        except RuntimeError as e:
            if coba == 2 or not any(k in str(e) for k in ("ProcessingFailed", " 50", "processing failed")):
                raise
            time.sleep(30)


def unggah_reel(ig_id, token, video, caption, jenis="REELS"):
    data = {"media_type": jenis, "upload_type": "resumable"}
    if jenis == "REELS":
        data.update(caption=caption, share_to_feed="true")
    w = ig("POST", f"{ig_id}/media", token, data=data)
    for coba in range(5):  # server Meta kadang 503 sesaat
        with open(video, "rb") as f:
            r = requests.post(w["uri"], data=f, timeout=900, headers={
                "Authorization": f"OAuth {token}", "offset": "0", "file_size": str(os.path.getsize(video))})
        if r.status_code < 500:
            break
        time.sleep(15 * (coba + 1))
    if r.status_code != 200:
        raise RuntimeError(f"upload video gagal {r.status_code}: {r.text[:300]}")
    for _ in range(90):
        s = ig("GET", w["id"], token, params={"fields": "status_code,status"})
        if s.get("status_code") == "FINISHED":
            break
        if s.get("status_code") in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"proses video gagal: {s.get('status')}")
        time.sleep(10)
    else:
        raise RuntimeError("proses video terlalu lama")
    m = ig("POST", f"{ig_id}/media_publish", token, data={"creation_id": w["id"]})
    return ig("GET", m["id"], token, params={"fields": "permalink"}).get("permalink", m["id"])


def cmd_posting(argumen):
    slot = argumen[0] if argumen else "19.00"
    jam, menit = map(int, slot.split("."))
    target = sekarang().replace(hour=jam, minute=menit, second=0, microsecond=0)
    tunggu = (target - sekarang()).total_seconds()
    if 0 < tunggu < 30 * 60:  # GitHub kadang jalan lebih awal; tunggu sampai jamnya
        time.sleep(tunggu)
    d = sekarang().date()
    TMP.mkdir(parents=True, exist_ok=True)
    gagal = 0
    for brand in FOLDER:
        ig_id = os.environ[f"IG_ID_{brand.upper()}"]
        token = os.environ.get(f"IG_TOKEN_{brand.upper()}") or os.environ["IG_TOKEN"]
        for f in folder_slot(d, brand, slot):
            isi = {x["name"]: x for x in gdrive.daftar(f["id"])}
            perlu_ig, perlu_fb = TANDA_TAYANG not in isi, TANDA_FB not in isi
            if not (perlu_ig or perlu_fb):
                lapor(f"SUDAH {brand}: {f['name']}")
                continue
            mp4 = [x for n, x in isi.items() if n.lower().endswith(".mp4")]
            if len(mp4) != 1 or "caption.txt" not in isi:
                lapor(f"LEWAT {brand}: {f['name']} (butuh 1 mp4 + caption.txt)")
                gagal += 1
                continue
            caption = gdrive.baca_teks(isi["caption.txt"]["id"]).strip()
            video = gdrive.unduh(mp4[0]["id"], TMP / "posting.mp4")
            if perlu_ig:
                try:
                    link = unggah_coba(ig_id, token, video, caption)
                    gdrive.tulis_teks(f["id"], TANDA_TAYANG, f"{sekarang():%d/%m/%Y %H:%M} WIB\n{link}\n")
                    lapor(f"TAYANG IG {brand}: {f['name']}\n{link}")
                except Exception as e:
                    lapor(f"GAGAL IG {brand}: {f['name']}: {e}")
                    gagal += 1
            if perlu_fb:
                try:
                    link = fb.reel(brand, os.environ["IG_TOKEN"], video, caption)
                    gdrive.tulis_teks(f["id"], TANDA_FB, f"{sekarang():%d/%m/%Y %H:%M} WIB\n{link}\n")
                    lapor(f"TAYANG FB {brand}: {f['name']}\n{link}")
                except Exception as e:  # FB gagal tidak membatalkan IG
                    lapor(f"GAGAL FB {brand}: {f['name']}: {e}")
    if gagal:
        raise SystemExit(f"{gagal} posting gagal")


# ---------------- story opening ----------------

def cmd_story(_):
    """10.00 WIB: story opening umum (video sama tiap hari) di Goldfish and Richman."""
    target = sekarang().replace(hour=10, minute=0, second=0, microsecond=0)
    tunggu = (target - sekarang()).total_seconds()
    if 0 < tunggu < 30 * 60:
        time.sleep(tunggu)
    token = os.environ.get("IG_TOKEN_GOLDFISH") or os.environ["IG_TOKEN"]
    link = unggah_reel(os.environ["IG_ID_GOLDFISH"], token, REPO / "aset/story/story opening.mp4", None, jenis="STORIES")
    lapor(f"STORY opening Goldfish and Richman tayang: {link}")
    try:
        lapor(f"STORY opening FB Goldfish and Richman: {fb.story('goldfish', os.environ['IG_TOKEN'], REPO / 'aset/story/story opening.mp4')}")
    except Exception as e:
        lapor(f"GAGAL story FB: {e}")


# ---------------- bersih ----------------

def cmd_bersih(_):
    hari_ini = sekarang().date()
    batas = hari_ini - dt.timedelta(days=7)
    bulan_ini = hari_ini.replace(day=1)
    for d in {bulan_ini, (bulan_ini - dt.timedelta(days=1)).replace(day=1)}:
        for brand in FOLDER:
            par = folder_brand(d, brand)
            if not par:
                continue
            for f in gdrive.daftar(par, True):
                m = POLA.match(f["name"])
                if not m:
                    continue
                try:
                    tgl = dt.date(d.year, int(m[2]), int(m[1]))
                except ValueError:
                    continue
                if tgl < batas and gdrive.cari(f["id"], TANDA_AGENT, folder=False):
                    gdrive.buang(f["id"])
                    lapor(f"DIBUANG ke Sampah: {FOLDER[brand]}/{f['name']}")


if __name__ == "__main__":
    perintah = {"buat": cmd_buat, "posting": cmd_posting, "bersih": cmd_bersih, "story": cmd_story}
    if len(sys.argv) < 2 or sys.argv[1] not in perintah:
        print(__doc__)
        sys.exit(1)
    try:
        perintah[sys.argv[1]](sys.argv[2:])
    finally:
        ringkas = os.environ.get("GITHUB_STEP_SUMMARY")
        if ringkas and laporan:
            with open(ringkas, "a", encoding="utf-8") as f:
                f.write("```\n" + "\n".join(laporan) + "\n```\n")
