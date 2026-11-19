"""Video footage (slot 19.00): potongan Stock Footage + teks kotak maroon + VO + musik + kartu logo.

python render/footage.py <spec.json> <fishtudio|goldfish> <folder klip> <folder kerja> <output.mp4>
spec: {"adegan": [{"vo": str, "teks": str}], "cta_vo": str, "cta_teks": str, "musik": str}
"""
import json
import os
import random
import shutil
import subprocess
import sys
import textwrap
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FONT = REPO / "aset/font/Poppins-Bold.ttf"
BRAND = {
    "fishtudio": {"logo": "fishtudio.png", "tagline": "Luxury living, inspired by nature", "bg": "black", "ink": "white"},
    "goldfish": {"logo": "goldfish.png", "tagline": "Goldfish & Richman by Fish Studio", "bg": "white", "ink": "0x0b0b0b"},
}
FPS, W, H = 30, 1080, 1920
VOICE, RATE = "id-ID-ArdiNeural", "+2%"


def run(*args):
    subprocess.run([str(a) for a in args], check=True, stdout=subprocess.DEVNULL)


def durasi(f):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def tts(teks, mp3, wav):
    for _ in range(15):
        try:
            subprocess.run(["edge-tts", "--voice", VOICE, f"--rate={RATE}", "--text", teks, "--write-media", str(mp3)],
                           check=True, capture_output=True, timeout=40)
            if mp3.exists() and mp3.stat().st_size > 2000:
                break
        except Exception:
            time.sleep(3)
    else:
        raise RuntimeError(f"edge-tts gagal: {teks}")
    tr = "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.03"
    run("ffmpeg", "-v", "error", "-y", "-i", mp3, "-af", f"{tr},areverse,{tr},areverse", "-ar", "44100", "-ac", "2", wav)
    return durasi(wav)


def teks_file(work, nama, teks, lebar=20):
    baris = []
    for b in teks.split("\n"):
        baris += textwrap.wrap(b, lebar) or [""]
    f = work / f"{nama}.txt"
    f.write_bytes("\n".join(baris[:3]).encode("utf-8"))  # LF saja, CRLF bikin drawtext renggang
    return f.name


def main(spec_path, brand, klip_dir, work, output):
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    B = BRAND[brand]
    work, output = Path(work).resolve(), Path(output).resolve()
    klip_dir = Path(klip_dir).resolve()
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    shutil.copy(FONT, work / "f.ttf")
    shutil.copy(REPO / "aset/logo" / B["logo"], work / "logo.png")
    os.chdir(work)  # drawtext memakai path relatif (f.ttf, t*.txt)

    klip = sorted(p for p in Path(klip_dir).iterdir() if p.suffix.lower() in (".mp4", ".mov"))
    if not klip:
        raise RuntimeError("tidak ada klip footage")
    random.shuffle(klip)

    # VO per kalimat
    kalimat = [a["vo"] for a in spec["adegan"]] + [spec["cta_vo"]]
    D = [tts(k, work / f"vo{i}.mp3", work / f"vo{i}.wav") for i, k in enumerate(kalimat)]

    # adegan: durasi = VO + jeda
    segmen, vo_mulai, t = [], [], 0.0
    for i, a in enumerate(spec["adegan"] + [{"teks": spec["cta_teks"], "cta": True}]):
        lead = 0.35 if i == 0 else 0.15
        dur = round(lead + D[i] + 0.45, 3)
        vo_mulai.append(t + lead)
        src = klip[i % len(klip)]
        panjang = durasi(src)
        mulai = random.uniform(0.3, max(0.3, panjang - dur - 0.3)) if panjang > dur + 0.6 else 0
        tf = teks_file(work, f"t{i}", a["teks"], 22 if a.get("cta") else 20)
        if a.get("cta"):
            gaya = (f"drawtext=fontfile=f.ttf:textfile={tf}:fontsize=84:fontcolor=white:line_spacing=20:"
                    f"x=(w-text_w)/2:y=(h-text_h)/2")
            gelap = ",eq=brightness=-0.25:saturation=0.8"
        else:
            gaya = (f"drawtext=fontfile=f.ttf:textfile={tf}:fontsize=74:fontcolor=white:line_spacing=16:box=1:"
                    f"boxcolor=0x8A0A0E@0.92:boxborderw=36:x=(w-text_w)/2:y=h*0.68")
            gelap = ""
        vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={FPS}{gelap},"
              f"zoompan=z='min(1+0.0008*on,1.06)':d=1:s={W}x{H}:fps={FPS},{gaya}")
        out = work / f"s{i}.mp4"
        run("ffmpeg", "-v", "error", "-y", "-ss", f"{mulai:.2f}", "-t", f"{dur}", "-i", src, "-an", "-vf", vf,
            "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", FPS, out)
        segmen.append(out)
        t += dur

    # kartu logo penutup
    tg = teks_file(work, "tag", B["tagline"], 60)
    logo_dur = 2.6
    run("ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"color=c={B['bg']}:s={W}x{H}:r={FPS}:d={logo_dur}",
        "-loop", "1", "-i", work / "logo.png", "-filter_complex",
        f"[1]scale=800:-1,format=rgba,fade=in:st=0:d=0.5:alpha=1[l];[0][l]overlay=(W-w)/2:(H-h)/2-80,"
        f"drawtext=fontfile=f.ttf:textfile={tg}:fontsize=44:fontcolor={B['ink']}:x=(w-text_w)/2:y=h/2+140",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p", "-t", logo_dur, work / "logo.mp4")
    segmen.append(work / "logo.mp4")
    total = t + logo_dur

    (work / "daftar.txt").write_text("".join(f"file '{s.name}'\n" for s in segmen), encoding="utf-8")
    run("ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", work / "daftar.txt", "-c", "copy", work / "video.mp4")

    # audio: VO di posisinya + musik 0,14 (input 0 = video, jadi indeks audio mulai 1)
    n = len(kalimat)
    ins = []
    for i in range(n):
        ins += ["-i", work / f"vo{i}.wav"]
    ins += ["-i", REPO / "aset/musik" / spec["musik"]]
    # input 0 = video, jadi indeks audio digeser satu
    fl2 = []
    for i in range(n):
        fl2.append(f"[{i + 1}]adelay={int(vo_mulai[i] * 1000)}:all=1[a{i}]")
    fl2.append("".join(f"[a{i}]" for i in range(n)) + f"amix=inputs={n}:normalize=0,loudnorm=I=-16:TP=-1.5[vo]")
    fl2.append(f"[{n + 1}]atrim=0:{total:.2f},volume=0.14,afade=t=in:d=0.4,afade=t=out:st={total - 2:.2f}:d=2[m]")
    fl2.append("[vo][m]amix=inputs=2:normalize=0:duration=longest[o]")
    run("ffmpeg", "-v", "error", "-y", "-i", work / "video.mp4", *ins, "-filter_complex", ";".join(fl2),
        "-map", "0:v", "-map", "[o]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-t", f"{total:.2f}",
        "-movflags", "+faststart", output)
    print(json.dumps({"ok": True, "durasi": round(total, 2), "output": str(output)}))


if __name__ == "__main__":
    main(*sys.argv[1:6])
