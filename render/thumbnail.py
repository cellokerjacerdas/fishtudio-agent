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


if __name__ == "__main__":
    spec, brand, jenis, sumber, keluar = sys.argv[1:6]
    print(buat(json.loads(Path(spec).read_text(encoding="utf-8")), brand, jenis, sumber, keluar))
