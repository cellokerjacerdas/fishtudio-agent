"""Posting ke Threads (mirror konten IG) untuk Fishtudio dan Goldfish and Richman.

Token Threads terpisah dari token Meta/IG: satu token per akun Threads, env user
THREADS_TOKEN_FISHTUDIO dan THREADS_TOKEN_GOLDFISH (diisi lewat `pasang token threads.bat`).
Token berlaku 60 hari dan diperpanjang otomatis oleh `perpanjang` (dipanggil upload.py cek tiap pagi).

Video Threads wajib berupa URL publik, jadi video diambil dari Reels IG yang baru tayang (media_url).
Teks: threads.txt di folder konten. Batas Threads 500 karakter per post, jadi narasi panjang
dipecah per paragraf: post pertama berisi video, sisanya jadi balasan berantai di bawahnya.
Kalau threads.txt tidak ada, narasi disusun dari isi caption.txt tanpa hashtag dan kredit musik.
"""
import re
import time

import requests

API = "https://graph.threads.net/v1.0"
BATAS = 500


def _req(metode, url, **kw):
    timeout = kw.pop("timeout", 60)
    for coba in range(4):  # server Meta kadang 5xx sesaat
        r = requests.request(metode, url, timeout=timeout, **kw)
        if r.status_code < 500:
            break
        time.sleep(10 * (coba + 1))
    try:
        d = r.json()
    except ValueError:
        d = {"raw": r.text[:300]}
    if r.status_code >= 400 or (isinstance(d, dict) and "error" in d):
        err = d.get("error", d) if isinstance(d, dict) else d
        raise RuntimeError(f"Threads {r.status_code}: {err.get('message', err) if isinstance(err, dict) else err}")
    return d


def perpanjang(token):
    """Tukar token long lived jadi token baru 60 hari. Token harus berumur minimal 24 jam."""
    d = _req("GET", f"{API.rsplit('/', 1)[0]}/refresh_access_token",
             params={"grant_type": "th_refresh_token", "access_token": token})
    return d["access_token"], int(d.get("expires_in", 0)) // 86400


def profil(token):
    return _req("GET", f"{API}/me", params={"fields": "id,username", "access_token": token})


def narasi_dari_caption(caption):
    """Cadangan kalau threads.txt tidak ada: buang hashtag, kredit musik, dan tagline."""
    buang = re.compile(r"^(#|music:|musik:|fishtudio\. luxury|goldfish & richman by)", re.I)
    paragraf = [p.strip() for p in caption.split("\n\n")]
    return "\n\n".join(p for p in paragraf if p and not buang.match(p))


def pecah(teks):
    """Pecah per paragraf jadi potongan maksimal 500 karakter."""
    potongan, kini = [], ""
    for p in [p.strip() for p in teks.strip().split("\n\n") if p.strip()]:
        while len(p) > BATAS:  # paragraf kepanjangan: potong di akhir kalimat terdekat
            titik = max(p.rfind(". ", 0, BATAS), p.rfind("? ", 0, BATAS), p.rfind("! ", 0, BATAS))
            titik = titik + 1 if titik > 0 else p.rfind(" ", 0, BATAS)
            if kini:
                potongan.append(kini)
                kini = ""
            potongan.append(p[:titik].strip())
            p = p[titik:].strip()
        if kini and len(kini) + 2 + len(p) > BATAS:
            potongan.append(kini)
            kini = p
        else:
            kini = f"{kini}\n\n{p}" if kini else p
    if kini:
        potongan.append(kini)
    return potongan


def _tunggu(cid, token):
    for _ in range(60):  # video diproses maksimal sekitar 10 menit
        s = _req("GET", f"{API}/{cid}", params={"fields": "status,error_message", "access_token": token})
        if s.get("status") == "FINISHED":
            return
        if s.get("status") in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Threads gagal memproses: {s.get('error_message') or s.get('status')}")
        time.sleep(10)
    raise RuntimeError("Threads memproses video terlalu lama")


def _terbit(uid, token, data):
    cid = _req("POST", f"{API}/{uid}/threads", params={"access_token": token}, data=data)["id"]
    _tunggu(cid, token)
    return _req("POST", f"{API}/{uid}/threads_publish", params={"access_token": token},
                data={"creation_id": cid})["id"]


def posting(token, teks, video_url=None):
    """Post utama (dengan video kalau ada) plus balasan berantai. Kembalikan permalink post utama."""
    uid = profil(token)["id"]
    bagian = pecah(teks) or [""]
    utama = {"media_type": "VIDEO", "video_url": video_url} if video_url else {"media_type": "TEXT"}
    pid = _terbit(uid, token, {**utama, "text": bagian[0]})
    induk = pid
    for b in bagian[1:]:
        induk = _terbit(uid, token, {"media_type": "TEXT", "text": b, "reply_to_id": induk})
    return _req("GET", f"{API}/{pid}", params={"fields": "permalink", "access_token": token}).get("permalink", pid)
