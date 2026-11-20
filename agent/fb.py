"""Posting ke Facebook Page (Reels dan Story video) dengan token pengguna sistem yang sama dengan Instagram.

Butuh izin pages_manage_posts + pages_read_engagement + pages_show_list, dan Page ditetapkan ke pengguna sistem.
Page dicari otomatis dari nama: "goldfish" -> goldfish, "fishtudio"/"fish studio" -> fishtudio.
"""
import os
import time

import requests

API = "https://graph.facebook.com/v23.0"
_page = {}


def _req(metode, url, **kw):
    timeout = kw.pop("timeout", 120)
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
        raise RuntimeError(f"FB {r.status_code}: {d.get('error', d) if isinstance(d, dict) else d}")
    return d


def page(brand, token):
    """(page_id, page_token) untuk brand 'goldfish' atau 'fishtudio'."""
    if brand in _page:
        return _page[brand]
    d = _req("GET", f"{API}/me/accounts", params={"access_token": token, "fields": "id,name,access_token", "limit": 100})
    for p in d.get("data", []):
        n = p["name"].lower()
        k = "goldfish" if "goldfish" in n else "fishtudio" if ("fishtudio" in n or "fish studio" in n) else None
        if k and k not in _page:
            _page[k] = (p["id"], p.get("access_token") or token)
    if brand not in _page:
        raise RuntimeError(f"Page FB {brand} belum ditetapkan ke pengguna sistem")
    return _page[brand]


def _unggah(edge, page_id, ptoken, video, extra_finish):
    mulai = _req("POST", f"{API}/{page_id}/{edge}", params={"access_token": ptoken}, data={"upload_phase": "start"})
    vid, url = mulai["video_id"], mulai["upload_url"]
    with open(video, "rb") as f:
        isi = f.read()
    _req("POST", url, data=isi, timeout=900, headers={
        "Authorization": f"OAuth {ptoken}", "offset": "0", "file_size": str(len(isi))})
    selesai = _req("POST", f"{API}/{page_id}/{edge}", params={"access_token": ptoken},
                   data={"upload_phase": "finish", "video_id": vid, **extra_finish})
    return selesai.get("post_id") or vid


def reel(brand, token, video, caption):
    pid, pt = page(brand, token)
    post = _unggah("video_reels", pid, pt, video, {"video_state": "PUBLISHED", "description": caption})
    return f"https://www.facebook.com/{pid}/videos/{post}" if str(post).isdigit() else str(post)


def story(brand, token, video):
    pid, pt = page(brand, token)
    return _unggah("video_stories", pid, pt, video, {})
