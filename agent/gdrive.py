"""Akses Google Drive lewat OAuth refresh token (akun Cello), pakai REST API langsung.

Env: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN
"""
import json
import os
import time
from pathlib import Path

import requests

API = "https://www.googleapis.com/drive/v3"
UPLOAD = "https://www.googleapis.com/upload/drive/v3/files"
FOLDER = "application/vnd.google-apps.folder"
_token = {"v": None, "exp": 0}


def token():
    if _token["v"] and time.time() < _token["exp"] - 60:
        return _token["v"]
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": os.environ["GOOGLE_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
        "refresh_token": os.environ["GOOGLE_REFRESH_TOKEN"],
        "grant_type": "refresh_token"}, timeout=30)
    r.raise_for_status()
    d = r.json()
    _token.update(v=d["access_token"], exp=time.time() + d.get("expires_in", 3600))
    return _token["v"]


def _h():
    return {"Authorization": f"Bearer {token()}"}


def _q(s):
    return s.replace("\\", "\\\\").replace("'", "\\'")


def daftar(parent, hanya_folder=None, nama=None):
    q = [f"'{parent}' in parents", "trashed = false"]
    if hanya_folder is True:
        q.append(f"mimeType = '{FOLDER}'")
    elif hanya_folder is False:
        q.append(f"mimeType != '{FOLDER}'")
    if nama is not None:
        q.append(f"name = '{_q(nama)}'")
    hasil, page = [], None
    while True:
        r = requests.get(f"{API}/files", headers=_h(), timeout=60, params={
            "q": " and ".join(q), "fields": "nextPageToken,files(id,name,mimeType,size,createdTime)",
            "pageSize": 1000, "pageToken": page, "supportsAllDrives": True, "includeItemsFromAllDrives": True})
        r.raise_for_status()
        d = r.json()
        hasil += d.get("files", [])
        page = d.get("nextPageToken")
        if not page:
            return hasil


def cari(parent, nama, folder=True):
    x = daftar(parent, folder, nama)
    return x[0]["id"] if x else None


def buat_folder(parent, nama):
    ada = cari(parent, nama)
    if ada:
        return ada
    r = requests.post(f"{API}/files", headers=_h(), timeout=60, params={"supportsAllDrives": True},
                      json={"name": nama, "mimeType": FOLDER, "parents": [parent]})
    r.raise_for_status()
    return r.json()["id"]


def jalur(*nama, buat=False, akar="root"):
    """Folder di My Drive berdasarkan urutan nama, contoh jalur('Fish Studio', '[02] CONTENT')."""
    cur = akar
    for n in nama:
        nxt = buat_folder(cur, n) if buat else cari(cur, n)
        if not nxt:
            return None
        cur = nxt
    return cur


def unggah(path, parent, nama=None, mime="application/octet-stream"):
    path = Path(path)
    meta = {"name": nama or path.name, "parents": [parent]}
    r = requests.post(f"{UPLOAD}?uploadType=resumable&supportsAllDrives=true", timeout=60,
                      headers={**_h(), "X-Upload-Content-Type": mime, "Content-Type": "application/json"},
                      data=json.dumps(meta))
    r.raise_for_status()
    with path.open("rb") as f:
        r2 = requests.put(r.headers["Location"], data=f, timeout=900, headers={"Content-Type": mime})
    r2.raise_for_status()
    return r2.json()["id"]


def tulis_teks(parent, nama, teks):
    tmp = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / f"_{nama}"
    tmp.write_text(teks, encoding="utf-8")
    return unggah(tmp, parent, nama, "text/plain")


def unduh(file_id, dest):
    with requests.get(f"{API}/files/{file_id}", headers=_h(), stream=True, timeout=900,
                      params={"alt": "media", "supportsAllDrives": True}) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for c in r.iter_content(1 << 20):
                f.write(c)
    return dest


def baca_teks(file_id):
    r = requests.get(f"{API}/files/{file_id}", headers=_h(), timeout=60, params={"alt": "media", "supportsAllDrives": True})
    r.raise_for_status()
    return r.content.decode("utf-8", "replace")


def buang(file_id):
    """Pindah ke Sampah (bisa dipulihkan 30 hari)."""
    r = requests.patch(f"{API}/files/{file_id}", headers=_h(), timeout=60, params={"supportsAllDrives": True},
                       json={"trashed": True})
    r.raise_for_status()
