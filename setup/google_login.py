"""Login Google sekali di laptop untuk mendapat refresh token Drive, lalu simpan ke GitHub Secrets.

Jalankan lewat "google login.bat". Butuh OAuth client tipe Desktop dari Google Cloud.
"""
import getpass
import http.server
import json
import subprocess
import sys
import threading
import urllib.parse
import urllib.request
import webbrowser

REPO = "cellokerjacerdas/fishtudio-agent"
GH = r"C:\Program Files\GitHub CLI\gh.exe"
SCOPE = "https://www.googleapis.com/auth/drive"

cid = input("Client ID: ").strip()
secret = getpass.getpass("Client secret (tidak tampil saat diketik): ").strip()
hasil = {}


class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        hasil.update({k: v[0] for k, v in q.items()})
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write("Login selesai. Tutup tab ini dan kembali ke jendela hitam.".encode())

    def log_message(self, *a):
        pass


srv = http.server.HTTPServer(("127.0.0.1", 0), H)
redirect = f"http://127.0.0.1:{srv.server_port}"
url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
    "client_id": cid, "redirect_uri": redirect, "response_type": "code", "scope": SCOPE,
    "access_type": "offline", "prompt": "consent", "login_hint": "cellokerjacerdas@gmail.com"})
print("\nBrowser akan terbuka. Login akun Google yang punya folder Fish Studio, lalu klik Izinkan.")
print("Kalau muncul 'Google belum memverifikasi aplikasi ini', klik Lanjutan lalu Buka (tidak aman).\n")
print(url, "\n")
webbrowser.open(url)
t = threading.Thread(target=srv.handle_request)
t.start()
t.join()
if "code" not in hasil:
    sys.exit(f"Login gagal: {hasil}")
data = urllib.parse.urlencode({"code": hasil["code"], "client_id": cid, "client_secret": secret,
                               "redirect_uri": redirect, "grant_type": "authorization_code"}).encode()
tok = json.load(urllib.request.urlopen("https://oauth2.googleapis.com/token", data))
if "refresh_token" not in tok:
    sys.exit(f"Tidak dapat refresh token: {tok}")

# uji: cari folder Fish Studio
q = urllib.parse.quote("name = 'Fish Studio' and 'root' in parents and trashed = false")
req = urllib.request.Request(f"https://www.googleapis.com/drive/v3/files?q={q}",
                             headers={"Authorization": f"Bearer {tok['access_token']}"})
files = json.load(urllib.request.urlopen(req)).get("files", [])
print("Folder Fish Studio ketemu." if files else "PERINGATAN: folder Fish Studio tidak ketemu di akun ini.")

for k, v in {"GOOGLE_CLIENT_ID": cid, "GOOGLE_CLIENT_SECRET": secret, "GOOGLE_REFRESH_TOKEN": tok["refresh_token"]}.items():
    subprocess.run([GH, "secret", "set", k, "--repo", REPO], input=v, text=True, check=True)
print("\nSelesai. Tiga rahasia Google tersimpan di GitHub.")
