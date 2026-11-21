"""Tema konten, dipakai bersama checker (evaluasi pagi 05.00) dan pembuat konten (08.00).

Footage memakai kategori dari bank naskah. Edukasi tidak punya kategori, jadi temanya
ditebak dari kata di judul. Urutan daftar penting: kata yang lebih khusus dicek dulu.
"""

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BANK = REPO / "data/bank.json"
POS = REPO / "data/bank_pos.json"
RIWAYAT = REPO / "data/riwayat.json"
EVALUASI = REPO / "data/evaluasi.json"
SLOT = {"edukasi": "12.00", "footage": "19.00"}
JENIS_SLOT = {v: k for k, v in SLOT.items()}

KATA_TEMA = {
    "fishtudio": [
        ("pakan", ["gold feeds", "pakan", "makan"]),
        ("kesehatan ikan", ["stres", "karantina", "mogok", "aklimatisasi", "kepadatan", "padat"]),
        ("alat akuarium", ["filter", "aerator", "oksigen", "lampu", "listrik"]),
        ("kualitas air", ["air", "pdam", "keruh", "hijau", "ph", "suhu", "lumut", "matahari"]),
        ("perawatan dan jasa", ["jasa", "perawatan", "cycling", "sifon", "tanaman", "liburan", "kesalahan", "pemula"]),
    ],
    "goldfish": [
        ("pakan", ["pakan", "porsi", "makan"]),
        ("kesehatan koki", ["bintik", "sirip", "mengapung", "diam di dasar", "memudar", "stres", "wen"]),
        ("beli dan pemula", ["pilih", "paket", "memasukkan", "pemula", "minta video", "menjaring", "kelas", "umur"]),
        ("kenal jenis", ["ciri", "beda", "jantan", "oranda", "ranchu", "ryukin", "panda"]),
        ("perawatan koki", ["akuarium", "filter", "air", "fishbowl", "dicampur", "kerikil", "dekorasi", "sejuk", "banyak"]),
    ],
}


def tema(brand, jenis, item):
    if jenis == "footage":
        return item.get("kategori") or "footage lain"
    judul = (item.get("judul") or "").lower()
    for nama, kata in KATA_TEMA.get(brand, []):
        if any(re.search(rf"\b{re.escape(k)}", judul) for k in kata):
            return nama
    return "edukasi lain"


def baca(p, bawaan):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return bawaan


def indeks_judul(bank):
    """judul -> (indeks hari, brand, jenis)."""
    out = {}
    for i, hari in enumerate(bank):
        for brand in ("fishtudio", "goldfish"):
            for jenis in SLOT:
                item = (hari.get(brand) or {}).get(jenis)
                if item:
                    out[norm(item["judul"])] = (i, brand, jenis)
    return out


def norm(judul):
    return re.sub(r"[^a-z0-9 ]", "", (judul or "").lower()).strip()


def tema_riwayat(entri, bank, idx=None):
    """Tema satu entri riwayat; entri lama belum menyimpan tema, jadi dicari lewat judulnya di bank."""
    if entri.get("tema"):
        return entri["tema"]
    idx = idx or indeks_judul(bank)
    hit = idx.get(norm(entri.get("judul")))
    if not hit:
        return None
    i, brand, jenis = hit
    return tema(brand, jenis, bank[i][brand][jenis])
