"""Thumbnail folder konten jadi cover Reels.

API Instagram hanya menerima cover dari URL publik, jadi thumbnail disisipkan sebagai frame awal video
(0,4 detik) lalu diunggah dengan thumb_offset=0. Permintaan Cello 21 Nov 2026.
Thumbnail = gambar (png/jpg/jpeg/webp) yang namanya mengandung "thumbnail", "thumb", atau "cover".
"""
import json
import re
import subprocess
from pathlib import Path

POLA = re.compile(r"thumb|cover", re.I)
EKST = (".png", ".jpg", ".jpeg", ".webp")
DURASI = 0.4


def cari(nama_file):
    """Dari daftar nama file, kembalikan nama thumbnail pertama atau None."""
    for n in sorted(nama_file):
        if n.lower().endswith(EKST) and POLA.search(n):
            return n
    return None


def sisipkan(video, gambar, keluar):
    video, gambar, keluar = Path(video), Path(gambar), Path(keluar)
    info = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,r_frame_rate",
                                      "-of", "json", str(video)], capture_output=True, text=True, check=True).stdout)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    ada_audio = any(s["codec_type"] == "audio" for s in info["streams"])
    w, h = v["width"], v["height"]
    a, b = (v.get("r_frame_rate") or "30/1").split("/")
    fps = round(int(a) / max(1, int(b))) or 30
    f = (f"[0:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1,fps={fps},format=yuv420p[c];"
         f"[1:v]setsar=1,fps={fps},format=yuv420p[v];[c][v]concat=n=2:v=1:a=0[vo]")
    peta = ["-map", "[vo]"]
    if ada_audio:
        f += f";[1:a]adelay={int(DURASI * 1000)}:all=1[ao]"
        peta += ["-map", "[ao]", "-c:a", "aac", "-b:a", "160k"]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-t", str(DURASI), "-i", str(gambar), "-i", str(video),
                    "-filter_complex", f, *peta, "-c:v", "libx264", "-crf", "18", "-preset", "fast",
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(keluar)], check=True)
    return keluar
