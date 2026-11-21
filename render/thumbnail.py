"""Thumbnail otomatis untuk tiap konten agent, disimpan sebagai "Thumbnail.png" di folder konten
(permintaan Cello 21 Nov 2026). Posting memakainya sebagai cover Reels lewat agent/cover.py.

python render/thumbnail.py <spec.json> <fishtudio|goldfish> <edukasi|footage> <video sumber> <out.png>

Format ikut .claude/rules/thumbnail-fish-studio.md: edukasi = gaya vlog stiker, footage = foto penuh + panel maroon.
Foto diambil dari klip sumber (bukan video jadi yang sudah berteks).
"""
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse
from pathlib import Path

DIR = Path(__file__).resolve().parent / "thumbnail"
HANDLE = {"fishtudio": "@fishtudio.richman", "goldfish": "@goldfishandrichman"}
LOGO = {"fishtudio": "fs", "goldfish": "gr"}
IKAN_KATEGORI = {"oranda": "oranda", "ryukin": "ryukin", "ranchu": "ranchu", "panda tanco": "ranchu",
                 "mas koki campur": "oranda"}
CHROME = [os.environ.get("CHROME", ""), r"C:\Program Files\Google\Chrome\Application\chrome.exe",
          r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe", "google-chrome", "google-chrome-stable",
          "chromium", "chromium-browser"]


def chrome():
    for c in CHROME:
        if c and (Path(c).exists() or shutil.which(c)):
            return c
    raise RuntimeError("Chrome tidak ketemu untuk render thumbnail")


def judul_besar(s):
    return " ".join(w[:1].upper() + w[1:] for w in s.split())


def dua_baris(headline):
    """'Terlalu padat, [ikan stres].' -> ('Terlalu Padat,', 'Ikan Stres'). Frasa kunci jadi baris besar."""
    h = headline.strip().rstrip(".!")
    m = re.match(r"^(.*?)\[(.+?)\](.*)$", h)
    if m:
        depan, kunci, belakang = (x.strip(" .") for x in m.groups())
        if depan:
            return judul_besar(depan), judul_besar(kunci)
        return judul_besar(kunci), judul_besar(belakang) if belakang else ""
    kata = h.split()
    if len(kata) <= 2:
        return "", judul_besar(h)
    # baris 2 hurufnya lebih besar, jadi dibuat lebih pendek: pilih potongan paling seimbang
    i = min(range(1, len(kata)), key=lambda i: max(len(" ".join(kata[:i])) * 0.74, len(" ".join(kata[i:]))))
    return judul_besar(" ".join(kata[:i])), judul_besar(" ".join(kata[i:]))


def _terang(video, t):
    """Rata-rata terang bagian atas frame (area di atas panel, y < 1240) pada detik t, 0-255."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1", "-vf",
                          "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,crop=1080:1000:0:240,"
                          "scale=54:50,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    return sum(raw) / len(raw) if raw else 0


def ambil_frame(video, out):
    """Frame paling terang dari lima titik, supaya subjek kelihatan (bukan frame gelap atau kosong)."""
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                str(video)], capture_output=True, text=True, check=True).stdout.strip() or 4)
    t = max((dur * k for k in (0.2, 0.35, 0.5, 0.65, 0.8)), key=lambda t: _terang(video, t))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1",
                    "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920", "-q:v", "2", str(out)],
                   check=True)
    return out


def data_thumbnail(item, brand, jenis, foto):
    d = {"b": LOGO[brand], "handle": HANDLE[brand], "foto": Path(foto).resolve().as_uri()}
    if jenis == "edukasi":
        d["f"] = "vlog"
        d["a"], d["k"] = dua_baris(item["adegan"][0]["headline"])
        angka = next((a["visual"] for a in item["adegan"] if a.get("visual", {}).get("jenis") == "angka"
                      and a["visual"].get("angka")), None)
        d["badge"] = [f'{angka["angka"]}{angka.get("satuan", "")}'] if angka else ["SAVE", "DULU"]
        if brand == "goldfish":
            d["ikan"] = random.choice(["oranda", "ryukin", "ranchu"])
    else:
        d["f"] = "cine"
        d["a"], d["k"] = dua_baris(item["adegan"][0]["teks"])
        d["ikan"] = IKAN_KATEGORI.get(item.get("kategori"))
    return d


def buat(item, brand, jenis, video_sumber, out):
    out = Path(out)
    kerja = Path(tempfile.mkdtemp(prefix="thumb"))
    try:
        foto = ambil_frame(video_sumber, kerja / "foto.jpg")
        d = data_thumbnail(item, brand, jenis, foto)
        url = (DIR / "thumbnail.html").resolve().as_uri() + "#" + urllib.parse.quote(json.dumps(d, ensure_ascii=False))
        png = kerja / "thumb.png"
        for coba in range(3):  # font Google kadang lambat, ulangi kalau gagal
            subprocess.run([chrome(), "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
                            "--allow-file-access-from-files", "--force-device-scale-factor=1",
                            f"--user-data-dir={kerja / 'profil'}", "--window-size=1080,1920",
                            "--virtual-time-budget=15000", f"--screenshot={png}", url],
                           capture_output=True, timeout=120)
            if png.exists() and png.stat().st_size > 50_000:
                break
            time.sleep(3)
        else:
            raise RuntimeError("render thumbnail gagal")
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(png), out)
        return out
    finally:
        shutil.rmtree(kerja, ignore_errors=True)


def sumber_edukasi(item, repo):
    """Klip latar video edukasi di aset/klip."""
    for ext in (".mp4", ".mov"):
        p = Path(repo) / "aset/klip" / f"{item['klip']}{ext}"
        if p.exists():
            return p
    return None


# ---------- thumbnail untuk folder yang belum punya (konten manual atau susulan) ----------

REPO = DIR.parent.parent
BRAND_FOLDER = {"Fishtudio": "fishtudio", "Goldfish and Richman": "goldfish"}
KATA_EDUKASI = re.compile(r"\b(edukasi|cara|ciri|tips|tanda|beda|funfact|fakta|kenapa|jangan|porsi)\b")
KATA_BUANG = re.compile(r"\b(edukasi|fishtudio|goldfish and richman|goldfish|richman)\b")


def _naskah_bank(brand, judul):
    try:
        bank = json.loads((REPO / "data/bank.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None, None
    for hari in bank:
        for jenis, it in hari.get(brand, {}).items():
            if re.sub(r"[^a-z0-9 ]", "", it["judul"].lower()).strip() == judul:
                return jenis, it
    return None, None


def buat_dari_folder(folder, brand=None, out_nama="Thumbnail.png"):
    """Thumbnail untuk folder konten [d m (HH.MM)] judul/ yang belum punya. Naskah bank dipakai kalau ada,
    kalau tidak judul diambil dari nama video dan fotonya dari video itu sendiri."""
    folder = Path(folder)
    brand = brand or BRAND_FOLDER.get(folder.parent.name, "fishtudio")
    video = next((f for f in sorted(folder.iterdir()) if f.suffix.lower() in (".mp4", ".mov")), None)
    if not video:
        raise RuntimeError("tidak ada video di folder")
    m = re.match(r"^\[[^\]]*\]\s*(.*)$", folder.name)
    judul = (m[1] if m else folder.name).strip().lower()
    jenis, item = _naskah_bank(brand, judul)
    if item:
        sumber = sumber_edukasi(item, REPO) if jenis == "edukasi" else video
        return buat(item, brand, jenis, sumber or video, folder / out_nama)
    teks = re.sub(r"\s+", " ", KATA_BUANG.sub("", video.stem.lower())).strip() or video.stem
    edukasi = bool(KATA_EDUKASI.search(video.stem.lower())) or " 12.00]" in folder.name
    if edukasi:
        item = {"adegan": [{"headline": teks, "visual": {}}]}
        return buat(item, brand, "edukasi", video, folder / out_nama)
    ikan = next((k for k in ("oranda", "ryukin", "ranchu") if k in teks), "oranda" if brand == "goldfish" else None)
    item = {"adegan": [{"teks": teks}], "kategori": ikan}
    return buat(item, brand, "footage", klip_stok(brand, ikan) or video, folder / out_nama)


STOK = Path(r"G:\My Drive\Fish Studio\[02] CONTENT\[00] Other\Stock Footage")
SUB_STOK = {"oranda": ["VIDEO IKAN/ORANDA"], "ryukin": ["VIDEO IKAN/RYUKIN"], "ranchu": ["VIDEO IKAN/RANCHU/Satuan"],
            "fishtudio": ["Footage Abe 9 Nov", "Footage 25 Okt/ngasih makan"]}


def klip_stok(brand, ikan):
    """Klip mentah dari Stock Footage (tanpa teks layar) untuk foto thumbnail footage; None kalau tidak ada (cloud)."""
    calon = []
    for sub in SUB_STOK.get(ikan or "fishtudio", []):
        if (STOK / sub).is_dir():
            calon += [f for f in (STOK / sub).iterdir() if f.suffix.lower() in (".mp4", ".mov")]
    if not calon:
        return None
    pilih = random.sample(calon, min(4, len(calon)))  # klip gelap sering ada, ambil yang paling terang

    def terang(f):
        try:
            return _terang(f, 1.5)
        except Exception:  # noqa: BLE001
            return 0
    return max(pilih, key=terang)


if __name__ == "__main__":
    spec, brand, jenis, sumber, keluar = sys.argv[1:6]
    print(buat(json.loads(Path(spec).read_text(encoding="utf-8")), brand, jenis, sumber, keluar))
