"""Claude menulis naskah + caption harian untuk Fishtudio dan Goldfish and Richman."""
import json

MODEL = "claude-opus-5-5"

KLIP_LATAR = ["akuarium oranda penuh", "akuarium ranchu", "kolam koki", "kolam koki ramai", "fish studio 1",
              "fish studio 2", "fish studio 4", "bongkar media filter", "servis ruang filter", "keranjang koki",
              "bak biru ranchu", "teras rumah klien"]
KATEGORI = {
    "fishtudio": ["kasih makan", "perawatan akuarium"],
    "goldfish": ["oranda", "ryukin", "ranchu", "panda tanco", "mas koki campur"],
}

ATURAN = """Kamu penulis konten harian Instagram untuk dua akun milik Fish Studio di Malang.

AKUN
1. Fishtudio (@fishtudio.richman): jasa perawatan dan pembuatan akuarium (Build & Care) dan pakan Gold Feeds.
   Gold Feeds = "pakan special untuk grooming" mas koki, Rp43 ribu per 300 g. Tagline: "Luxury living, inspired by nature."
   Topik edukasi: perawatan akuarium, kualitas air, filter, pakan, kebiasaan ikan hias, kesalahan pemula.
2. Goldfish and Richman (@goldfishandrichman): toko mas koki (oranda, ryukin, ranchu, panda, tanco) di Malang.
   Topik edukasi: jenis mas koki, cara memilih, cara merawat, ciri ikan sehat, tips pengiriman, kesalahan pemula.
WA untuk keduanya: 08569990738.

DUA JENIS VIDEO PER AKUN PER HARI
- "edukasi" (tayang 12.00): motion graphic. 3 atau 4 adegan. Tiap adegan: satu kalimat VO dan headline layar.
  Headline maksimal 6 kata, frasa kunci dalam kurung siku, contoh: "Ganti air [jangan dikuras] semua."
  Visual adegan pilih salah satu: "salah" (akuarium dicoret, untuk larangan), "benar" (akuarium dicentang),
  "angka" (angka besar + label pendek; isi angka dan satuan, contoh angka "30" satuan "%" label "air per minggu"),
  "daftar" (2 atau 3 poin, tiap poin maksimal 3 kata), "akuarium" (ikan berenang, netral).
  Pilih klip latar yang cocok dari daftar yang diberikan.
- "footage" (tayang 19.00): potongan video asli ikan atau kegiatan toko. 3 adegan. Tiap adegan: satu kalimat VO
  dan teks layar maksimal 7 kata. Pilih kategori footage dari daftar milik akun itu.
- Tiap kalimat VO maksimal 12 kata, bahasa lisan santai tapi sopan. Total video maksimal 25 detik.
- cta_vo: satu kalimat ajakan, contoh Fishtudio "Hubungi Fishtudio untuk perawatan akuariummu."
  cta_teks: teks layar ajakan, maksimal 6 kata, nama brand dalam kurung siku untuk edukasi.
  Di VO tulis "akuariummu" (satu kata), bukan "akuarium mu".

CAPTION (isi saja; tagline, kredit musik, dan hashtag ditambahkan sistem)
- Baris pertama maksimal 120 karakter dan berisi satu ajakan: chat WA 08569990738 dengan satu kata kunci
  huruf besar tanpa spasi (contoh RAWAT, ORANDA). Video sudah membawa hook, jadi baris pertama = ajakan + konteks.
- Lalu 2 sampai 3 paragraf pendek, dipisah satu baris kosong. Masukkan frasa yang dicari orang secara wajar,
  contoh "jasa perawatan akuarium di Malang", "mas koki oranda Malang".
- Hanya satu ajakan di seluruh caption. Tanpa link, tanpa hashtag, tanpa emoji.
- tagar_topik: satu hashtag topik tambahan untuk Fishtudio saja (tanpa tanda #, huruf kecil), contoh "perawatanakuarium".

LARANGAN (semua teks: VO, layar, caption)
- Tanpa emoji. Tanpa tanda pisah (-, –, —) sebagai pemisah kalimat; pakai titik atau koma.
- Jangan tulis "si jambul", "Molly Feeds", "Koi Feeds", "empat brand", harga selain Gold Feeds Rp43 ribu per 300 g.
- Jangan klaim yang perlu bukti: ikan hasil ternak sendiri, bahan pakan dari ikan sortiran, kadar protein,
  "delapan tahun", pernah ekspor, harga ikan.
- Ikan selalu di akuarium kaca kotak, jangan menyebut akuarium bulat atau fishbowl kecuali sedang melarangnya.
- Jangan mengulang judul atau sudut yang sudah dipakai (daftar riwayat diberikan).
- judul: 3 sampai 6 kata, huruf kecil, tanpa tanda baca, untuk nama folder.
"""


def _skema():
    visual = {"type": "object", "additionalProperties": False,
              "required": ["jenis", "angka", "satuan", "label", "poin"],
              "properties": {"jenis": {"type": "string", "enum": ["salah", "benar", "angka", "daftar", "akuarium"]},
                             "angka": {"type": "string"}, "satuan": {"type": "string"},
                             "label": {"type": "string"}, "poin": {"type": "array", "items": {"type": "string"}}}}
    edukasi = {"type": "object", "additionalProperties": False,
               "required": ["judul", "klip", "adegan", "cta_vo", "cta_teks", "caption", "tagar_topik"],
               "properties": {"judul": {"type": "string"}, "klip": {"type": "string", "enum": KLIP_LATAR},
                              "adegan": {"type": "array", "items": {
                                  "type": "object", "additionalProperties": False,
                                  "required": ["vo", "headline", "visual"],
                                  "properties": {"vo": {"type": "string"}, "headline": {"type": "string"},
                                                 "visual": visual}}},
                              "cta_vo": {"type": "string"}, "cta_teks": {"type": "string"},
                              "caption": {"type": "string"}, "tagar_topik": {"type": "string"}}}

    def footage(brand):
        return {"type": "object", "additionalProperties": False,
                "required": ["judul", "kategori", "adegan", "cta_vo", "cta_teks", "caption", "tagar_topik"],
                "properties": {"judul": {"type": "string"},
                               "kategori": {"type": "string", "enum": KATEGORI[brand]},
                               "adegan": {"type": "array", "items": {
                                   "type": "object", "additionalProperties": False, "required": ["vo", "teks"],
                                   "properties": {"vo": {"type": "string"}, "teks": {"type": "string"}}}},
                               "cta_vo": {"type": "string"}, "cta_teks": {"type": "string"},
                               "caption": {"type": "string"}, "tagar_topik": {"type": "string"}}}

    def akun(brand):
        return {"type": "object", "additionalProperties": False, "required": ["edukasi", "footage"],
                "properties": {"edukasi": edukasi, "footage": footage(brand)}}

    return {"type": "object", "additionalProperties": False, "required": ["fishtudio", "goldfish"],
            "properties": {"fishtudio": akun("fishtudio"), "goldfish": akun("goldfish")}}


def buat_rencana(tanggal_teks, riwayat, catatan=""):
    import anthropic  # hanya dipakai kalau bank naskah habis dan ANTHROPIC_API_KEY ada

    client = anthropic.Anthropic()
    pakai = "\n".join(f"- {r['brand']} {r['slot']}: {r['judul']}" for r in riwayat[-120:]) or "(belum ada)"
    pesan = (f"Tanggal tayang: {tanggal_teks}.\n\nRiwayat judul yang sudah dipakai:\n{pakai}\n\n"
             f"Klip latar edukasi yang tersedia: {', '.join(KLIP_LATAR)}.\n"
             f"Kategori footage Fishtudio: {', '.join(KATEGORI['fishtudio'])}. "
             f"Kategori footage Goldfish and Richman: {', '.join(KATEGORI['goldfish'])}.\n\n"
             "Tulis 4 konten untuk hari ini: edukasi dan footage untuk masing-masing akun. "
             "Variasikan topik dan jenis visual antar konten." + (f"\n\nCatatan perbaikan: {catatan}" if catatan else ""))
    resp = client.beta.messages.create(
        model=MODEL,
        max_tokens=16000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        output_config={"effort": "medium", "format": {"type": "json_schema", "schema": _skema()}},
        system=ATURAN,
        messages=[{"role": "user", "content": pesan}],
    )
    if resp.stop_reason == "refusal":
        raise RuntimeError(f"Claude menolak: {resp.stop_details}")
    if resp.stop_reason == "max_tokens":
        raise RuntimeError("jawaban Claude terpotong (max_tokens)")
    teks = next(b.text for b in resp.content if b.type == "text")
    return json.loads(teks)
