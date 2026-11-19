"""Periksa bank naskah sebelum dipakai agent.

python setup/cek_bank.py data/bank.json   (atau file bagian)
Keluar kode 1 kalau ada SALAH.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "agent"))
from rencana import KATEGORI, KLIP_LATAR  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿️]")
DASH = re.compile(r"—|–|\s-\s")
LARANG = [r"si jambul", r"molly feeds", r"koi feeds", r"(empat|4) brand", r"ternak sendiri", r"hasil ternak",
          r"sortiran", r"protein\s*\d", r"(delapan|8)\s+tahun", r"ekspor", r"https?://", r"#"]
salah = []


def kata(s):
    return len(re.sub(r"[\[\]]", "", s).split())


def cek_teks(lok, s, maks_kata=None):
    if not s or not s.strip():
        salah.append(f"{lok}: kosong")
        return
    if EMOJI.search(s):
        salah.append(f"{lok}: ada emoji")
    if DASH.search(s):
        salah.append(f"{lok}: tanda pisah")
    for p in LARANG:
        if re.search(p, s, re.I):
            salah.append(f"{lok}: kata terlarang /{p}/")
    if maks_kata and kata(s) > maks_kata:
        salah.append(f"{lok}: {kata(s)} kata (maks {maks_kata})")


def cek_item(lok, brand, jenis, it):
    cek_teks(f"{lok} judul", it["judul"], 7)
    if re.search(r"[^a-z0-9 ]", it["judul"]):
        salah.append(f"{lok} judul: hanya huruf kecil, angka, spasi")
    ad = it["adegan"]
    if jenis == "edukasi":
        if not 3 <= len(ad) <= 4:
            salah.append(f"{lok}: adegan edukasi harus 3-4")
        if it["klip"] not in KLIP_LATAR:
            salah.append(f"{lok}: klip '{it['klip']}' tidak dikenal")
        for i, a in enumerate(ad):
            cek_teks(f"{lok} adegan{i} vo", a["vo"], 12)
            cek_teks(f"{lok} adegan{i} headline", a["headline"], 6)
            if "[" not in a["headline"]:
                salah.append(f"{lok} adegan{i}: headline tanpa [frasa kunci]")
            v = a["visual"]
            if v["jenis"] not in ("salah", "benar", "angka", "daftar", "akuarium"):
                salah.append(f"{lok} adegan{i}: visual '{v['jenis']}'")
            if v["jenis"] == "angka" and not v.get("angka"):
                salah.append(f"{lok} adegan{i}: angka kosong")
            if v["jenis"] == "angka":
                cek_teks(f"{lok} adegan{i} label", v.get("label", ""), 4)
            if v["jenis"] == "daftar":
                if not 2 <= len(v.get("poin", [])) <= 3:
                    salah.append(f"{lok} adegan{i}: poin daftar harus 2-3")
                for p in v.get("poin", []):
                    cek_teks(f"{lok} adegan{i} poin", p, 3)
    else:
        if len(ad) != 3:
            salah.append(f"{lok}: adegan footage harus 3")
        if it["kategori"] not in KATEGORI[brand]:
            salah.append(f"{lok}: kategori '{it['kategori']}' bukan milik {brand}")
        for i, a in enumerate(ad):
            cek_teks(f"{lok} adegan{i} vo", a["vo"], 12)
            cek_teks(f"{lok} adegan{i} teks", a["teks"], 7)
    cek_teks(f"{lok} cta_vo", it["cta_vo"], 12)
    cek_teks(f"{lok} cta_teks", it["cta_teks"], 6)
    if "akuarium mu" in it["cta_vo"].lower():
        salah.append(f"{lok} cta_vo: tulis 'akuariummu'")
    cap = it["caption"]
    cek_teks(f"{lok} caption", cap)
    baris1 = cap.strip().split("\n")[0]
    if len(baris1) > 120:
        salah.append(f"{lok} caption: baris pertama {len(baris1)} karakter (maks 120)")
    if "08569990738" not in baris1:
        salah.append(f"{lok} caption: baris pertama tanpa WA 08569990738")
    if not re.search(r"\b[A-Z]{3,}\b", baris1):
        salah.append(f"{lok} caption: baris pertama tanpa KATA KUNCI huruf besar")
    if len(cap) > 1200:
        salah.append(f"{lok} caption: terlalu panjang ({len(cap)})")
    if brand == "fishtudio" and not re.fullmatch(r"[a-z0-9]+", it.get("tagar_topik", "")):
        salah.append(f"{lok}: tagar_topik harus huruf kecil tanpa spasi")


def main(path):
    hari = json.loads(Path(path).read_text(encoding="utf-8"))
    judul = {}
    for h, d in enumerate(hari, 1):
        for brand in ("fishtudio", "goldfish"):
            for jenis in ("edukasi", "footage"):
                lok = f"hari{h} {brand} {jenis}"
                try:
                    it = d[brand][jenis]
                    cek_item(lok, brand, jenis, it)
                    if it["judul"] in judul:
                        salah.append(f"{lok}: judul sama dengan {judul[it['judul']]}")
                    judul[it["judul"]] = lok
                except KeyError as e:
                    salah.append(f"{lok}: field hilang {e}")
    # cek.js aturan brand
    semua = "\n".join(json.dumps(d, ensure_ascii=False) for d in hari)
    tmp = REPO / "_tmp_cek.txt"
    tmp.write_text(semua, encoding="utf-8")
    r = subprocess.run(["node", str(REPO / "agent/cek.js"), str(tmp)], capture_output=True, text=True, encoding="utf-8")
    tmp.unlink()
    for b in r.stdout.splitlines():
        if re.search(r"^\s*\d+: SALAH", b):
            salah.append("cek.js " + b.strip())
    print(f"{len(hari)} hari, {len(judul)} konten, {len(salah)} masalah")
    for s in salah:
        print(" ", s)
    sys.exit(1 if salah else 0)


if __name__ == "__main__":
    main(sys.argv[1])
