// Cek copy Fishtudio terhadap keputusan brand. Keluar dengan kode 1 kalau ada SALAH.
// Jalankan: node cek.js "<file>" ["<file>" ...]
const fs = require("fs");
const path = require("path");

// SALAH = melanggar keputusan Cello. BUKTI = klaim yang perlu dokumen sebelum tayang.
const ATURAN = [
  ["SALAH", /si jambul/i, "Dilarang. Gold Feeds = pakan special untuk grooming"],
  ["SALAH", /molly feeds/i, "Molly Feeds dihapus sejak 26 Oktober 2026"],
  ["SALAH", /(empat|4) brand/i, "Struktur sekarang: induk Fish Studio dan dua brand ikan"],
  ["SALAH", /Rp\s?95(\.000| ?r)/i, "Harga lama. Gold Feeds Rp43 ribu per 300 g"],
  ["SALAH", /\p{Extended_Pictographic}/u, "Tanpa emoji"],
  ["SALAH", /—|–|\s-\s/, "Tanpa tanda pisah sebagai pemisah kalimat"],
  ["CEK", /koi feeds/i, "Koi Feeds belum diputuskan"],
  ["CEK", /fish ?bowl|akuarium bulat/i, "Ikan selalu di akuarium kaca kotak, kecuali konten yang memang membahas akuarium bulat"],
  ["BUKTI", /(besarkan|ternak|biakkan|breeding)\s+(kami\s+)?sendiri|hasil ternak/i, "Sebagian ikan dibeli. Pastikan klaim ini benar untuk ikan yang dimaksud"],
  ["BUKTI", /sortiran/i, "Budget mencatat beli pakan 40 kg. Pastikan bahannya memang dari ikan sortiran"],
  ["BUKTI", /protein\s*\d+/i, "Perlu spesifikasi atau hasil uji"],
  ["BUKTI", /(delapan|8)\s+tahun/i, "Pastikan dasar hitungan tahunnya"],
  ["BUKTI", /mulai\s+Rp\s?350|Rp\s?350\s*(ribu|rb)/i, "Harga rata-rata terjual jauh di bawah ini. Sesuaikan dengan daftar harga terbaru"],
  ["BUKTI", /pernah ekspor|riwayat ekspor/i, "Pastikan bisa dibuktikan"],
];

const TIDAK_DICEK = /^\s*(#|-\s|\d+\.\s|Status:)|^\s*\|/;
let salah = 0, total = 0;

for (const file of process.argv.slice(2)) {
  const baris = fs.readFileSync(file, "utf8").split(/\r?\n/);
  console.log(path.basename(file));
  let temuan = 0;
  baris.forEach((teks, i) => {
    ATURAN.forEach(([tingkat, pola, pesan]) => {
      // tanda pisah di judul, daftar, dan tabel bukan copy yang tayang
      if (pesan.startsWith("Tanpa tanda pisah") && TIDAK_DICEK.test(teks)) return;
      const m = teks.match(pola);
      if (!m) return;
      temuan++; total++;
      if (tingkat === "SALAH") salah++;
      console.log(`  ${i + 1}: ${tingkat} "${m[0].trim() || m[0]}". ${pesan}`);
    });
  });
  // Hashtag wajib per brand (rules/caption-fishtudio.md), hanya untuk file caption*
  if (/^caption/i.test(path.basename(file))) {
    const lokasi = path.resolve(file).replace(/\\/g, "/");
    const isi = baris.join("\n");
    const brand = /Goldfish and Richman/i.test(lokasi) ? "GR"
      : /\/Fishtudio\//i.test(lokasi) ? "FS"
      : /goldfishandrichman|Goldfish & Richman/i.test(isi) ? "GR" : "FS";
    const wajib = brand === "GR"
      ? ["#goldfishindonesia", "#goldfishmalang", "#maskokiindonesia", "#maskokimalang", "#goldfishandrichman"]
      : ["#Fishtudio", "#Aquariummalang", "#Perawatanaquariumindonesia", "#Aquascape"];
    const tags = isi.match(/#\w+/g) || [];
    wajib.filter((t) => !tags.includes(t)).forEach((t) => {
      temuan++; total++; salah++;
      console.log(`  SALAH hashtag wajib ${brand === "GR" ? "Goldfish and Richman" : "Fishtudio"} belum ada: ${t}`);
    });
    const kecil = tags.map((t) => t.toLowerCase());
    const ganda = [...new Set(kecil.filter((t, i) => kecil.indexOf(t) !== i))];
    if (ganda.length) { temuan++; total++; console.log(`  CEK hashtag ganda: ${ganda.join(" ")}`); }
  }
  if (!temuan) console.log("  Bersih");
}
console.log(`\n${total} temuan, ${salah} SALAH`);
process.exit(salah ? 1 : 0);
