// Menyusun SFX (cues.json), VO (audio/vo.wav), dan musik ke audio/mix.wav.
// node render/mix.cjs <folder kerja> <musik.mp3>
// Setelan Cello 19 Nov 2026: SFX halus (klik, ketukan kayu), musik ~0,14 di bawah VO.
const { execFileSync } = require("child_process");
const fs = require("fs"), path = require("path");
const [, , work, music] = process.argv;
const { end, cues } = JSON.parse(fs.readFileSync(path.join(work, "cues.json"), "utf8"));
const SR = 44100, N = Math.ceil(end * SR);
const out = [new Float32Array(N), new Float32Array(N)];
const cache = {};
const SFX = 0.4;
function load(f, extra = []) {
  const key = f + extra.join(" ");
  if (cache[key]) return cache[key];
  const b = execFileSync("ffmpeg", ["-v", "error", ...extra, "-i", f, "-f", "f32le", "-ar", String(SR), "-ac", "2", "-"], { maxBuffer: 1 << 30 });
  const a = new Float32Array(b.buffer.slice(b.byteOffset, b.byteOffset + b.length));
  let pk = 0; for (const v of a) pk = Math.max(pk, Math.abs(v));
  return (cache[key] = { a, pk: pk || 1 });
}
for (const [name, t, g, r = 1] of cues) {
  const s = load(path.join(work, "audio/sfx", name + ".wav"));
  const len = Math.floor(s.a.length / 2 / r), st = Math.round(t * SR);
  for (let i = 0; i < len && st + i < N; i++) {
    if (st + i < 0) continue;
    const q = i * r, j = Math.floor(q), f = q - j, fo = Math.min(1, (len - i) / 200);
    for (let c = 0; c < 2; c++) out[c][st + i] += (((s.a[j * 2 + c] || 0) * (1 - f) + (s.a[(j + 1) * 2 + c] || 0) * f) / s.pk) * g * fo * SFX;
  }
}
const vo = path.join(work, "audio/vo.wav");
if (fs.existsSync(vo)) {
  const v = load(vo);
  for (let i = 0; i < N && i * 2 + 1 < v.a.length; i++) for (let c = 0; c < 2; c++) out[c][i] += (v.a[i * 2 + c] / v.pk) * 0.9;
}
if (music && fs.existsSync(music)) {
  const VOL = 0.14, FI = 0.4, FO = 2.0;
  const m = load(music, ["-t", String(end + 1)]);
  for (let i = 0; i < N && i * 2 + 1 < m.a.length; i++) {
    const t = i / SR, f = Math.max(0, Math.min(1, t / FI, (end - t) / FO));
    out[0][i] += m.a[i * 2] * VOL * f; out[1][i] += m.a[i * 2 + 1] * VOL * f;
  }
}
let pk = 0; for (const c of out) for (const v of c) pk = Math.max(pk, Math.abs(v));
const norm = Math.min(1.2, 0.89 / (pk || 1));
const pcm = Buffer.alloc(N * 4);
for (let i = 0; i < N; i++) for (let c = 0; c < 2; c++) pcm.writeInt16LE(Math.max(-32768, Math.min(32767, Math.round(out[c][i] * norm * 32767))), (i * 2 + c) * 2);
const h = Buffer.alloc(44); h.write("RIFF", 0); h.writeUInt32LE(36 + pcm.length, 4); h.write("WAVEfmt ", 8); h.writeUInt32LE(16, 16); h.writeUInt16LE(1, 20); h.writeUInt16LE(2, 22); h.writeUInt32LE(SR, 24); h.writeUInt32LE(SR * 4, 28); h.writeUInt16LE(4, 32); h.writeUInt16LE(16, 34); h.write("data", 36); h.writeUInt32LE(pcm.length, 40);
fs.writeFileSync(path.join(work, "audio/mix.wav"), Buffer.concat([h, pcm]));
console.log("mix", cues.length, "cues, end", end);
