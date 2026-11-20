"""Story opening toko (9:16, 8 detik): footage ikan + STORE OPEN + hari/tanggal + WA + logo.

python render/story.py <folder klip> <output.mp4> [YYYY-MM-DD]
Area aman story: teks di antara y 300 dan 1600 (atas/bawah tertutup UI Instagram).
"""
import datetime as dt
import os
import random
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
BULAN = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober",
         "November", "Desember"]
DUR, W, H = 8, 1080, 1920


def durasi(f):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                                capture_output=True, text=True, check=True).stdout.strip())


def main(klip_dir, output, tanggal=None):
    d = dt.date.fromisoformat(tanggal) if tanggal else dt.date.today()
    output = Path(output).resolve()
    klip = [p for p in Path(klip_dir).resolve().iterdir() if p.suffix.lower() in (".mp4", ".mov")]
    random.seed(d.toordinal())  # klip berganti tiap hari, tetap sama kalau diulang di hari yang sama
    src = random.choice(klip)
    mulai = random.uniform(0.5, max(0.5, durasi(src) - DUR - 0.5))
    musik = REPO / "aset/musik" / random.choice(["goldfish carefree.mp3", "goldfish easy lemon.mp3", "goldfish wallpaper.mp3"])

    work = output.parent / "_story"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True, exist_ok=True)
    shutil.copy(REPO / "aset/font/Poppins-Bold.ttf", work / "f.ttf")
    shutil.copy(REPO / "aset/logo/goldfish.png", work / "logo.png")
    (work / "a.txt").write_bytes(b"STORE")
    (work / "b.txt").write_bytes(b"OPEN")
    (work / "c.txt").write_bytes(f"{HARI[d.weekday()]}, {d.day} {BULAN[d.month - 1]}".encode())
    (work / "d.txt").write_bytes("Mas koki ready hari ini".encode())
    (work / "e.txt").write_bytes("Chat WA 0856 9990 738".encode())
    os.chdir(work)

    teks = lambda f, size, y, t0, warna="white", extra="": (  # noqa: E731
        f"drawtext=fontfile=f.ttf:textfile={f}:fontsize={size}:fontcolor={warna}:x=(w-text_w)/2:y={y}{extra}:"
        f"alpha='if(lt(t,{t0}),0,min(1,(t-{t0})/0.35))'")
    vf = ";".join([
        f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=30,"
        f"zoompan=z='min(1+0.0012*on,1.08)':d=1:s={W}x{H}:fps=30,"
        f"drawbox=x=0:y=0:w={W}:h={H}:color=black@0.42:t=fill,"
        + ",".join([
            teks("a.txt", 230, 600, 0.2),
            teks("b.txt", 230, 840, 0.45),
            teks("c.txt", 64, 1120, 0.9),
            teks("d.txt", 52, 1210, 1.2),
            teks("e.txt", 60, 1370, 1.6, extra=":box=1:boxcolor=0x8A0A0E@0.95:boxborderw=34"),
        ]) + "[v0]",
        # logo G&R bertulisan hitam, jadi ditaruh di kartu putih
        "[1]scale=560:-1[lg];color=c=white:s=640x230:d=8,format=rgba[kartu];[kartu][lg]overlay=(W-w)/2:(H-h)/2[lk]",
        f"[v0][lk]overlay=(W-w)/2:310:enable='gte(t,0.1)'[v]",
        f"[2:a]atrim=0:{DUR},volume=0.5,afade=t=in:d=0.3,afade=t=out:st={DUR - 1.2}:d=1.2[a]",
    ])
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{mulai:.2f}", "-t", str(DUR), "-i", str(src),
                    "-loop", "1", "-i", "logo.png", "-i", str(musik), "-filter_complex", vf,
                    "-map", "[v]", "-map", "[a]", "-t", str(DUR), "-c:v", "libx264", "-preset", "fast", "-crf", "20",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(output)],
                   check=True)
    os.chdir(output.parent)
    shutil.rmtree(work, ignore_errors=True)
    print(output)


if __name__ == "__main__":
    main(*sys.argv[1:4])
