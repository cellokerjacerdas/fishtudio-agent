// Generator video edukasi motion graphic (slot 12.00) dari spec JSON buatan Claude.
// Pakai mesin edu.js dari project "hyperframes edukasi ganti air" (headline per kata, kartu 3D,
// akuarium SVG, ending CTA + logo + tagline). VO edge-tts Ardi +2%, musik di bawah VO.
//
// node render/edukasi.cjs <spec.json> <brand: fishtudio|goldfish> <folder kerja> <output.mp4>
const { execFileSync } = require("child_process");
const fs = require("fs"), path = require("path");

const [, , specPath, brand, work, output] = process.argv;
const spec = JSON.parse(fs.readFileSync(specPath, "utf8"));
const HERE = __dirname, REPO = path.join(HERE, "..");
const B = {
  fishtudio: { logo: "fishtudio.png", tagline: "Luxury living, inspired by nature", endBg: "#000", endInk: "#fff", ctaKlip: "fish studio 1" },
  goldfish: { logo: "goldfish.png", tagline: "Goldfish & Richman by Fish Studio", endBg: "#fff", endInk: "#0b0b0b", ctaKlip: "kolam koki ramai" },
}[brand];
if (!B) throw new Error("brand tidak dikenal: " + brand);

const sh = (cmd, args, opt = {}) => (execFileSync(cmd, args, { stdio: ["ignore", "pipe", "inherit"], ...opt }) ?? "").toString();
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

// ---------- siapkan folder kerja ----------
fs.rmSync(work, { recursive: true, force: true });
for (const d of ["audio/sfx", "audio/vo", "clips", "img", "fonts"]) fs.mkdirSync(path.join(work, d), { recursive: true });
for (const f of ["edu.js", "edu.css"]) fs.copyFileSync(path.join(HERE, "edukasi", f), path.join(work, f));
for (const f of fs.readdirSync(path.join(HERE, "edukasi/fonts"))) fs.copyFileSync(path.join(HERE, "edukasi/fonts", f), path.join(work, "fonts", f));
for (const f of fs.readdirSync(path.join(HERE, "edukasi/sfx"))) fs.copyFileSync(path.join(HERE, "edukasi/sfx", f), path.join(work, "audio/sfx", f));
fs.copyFileSync(path.join(REPO, "aset/logo", B.logo), path.join(work, "img/logo.png"));

const klipDir = path.join(REPO, "aset/klip");
const klip = (n) => { const f = path.join(klipDir, n + ".mp4"); return fs.existsSync(f) ? f : path.join(klipDir, fs.readdirSync(klipDir)[0]); };
// latar = klip + versi terbalik (supaya cukup panjang dan mulus)
sh("ffmpeg", ["-v", "error", "-y", "-i", klip(spec.klip), "-filter_complex", "[0:v]split[a][b];[b]reverse[r];[a][r]concat=n=2:v=1:a=0[v]", "-map", "[v]", "-an", "-c:v", "libx264", "-crf", "26", "-pix_fmt", "yuv420p", path.join(work, "clips/bg.mp4")]);
fs.copyFileSync(klip(B.ctaKlip), path.join(work, "clips/cta.mp4"));

// ---------- VO ----------
const lines = [...spec.adegan.map((a) => a.vo), spec.cta_vo];
const RATE = "+2%", VOICE = "id-ID-ArdiNeural", LEAD = 0.3, GAP = 0.4, GAP_CTA = 0.6;
const S = [], D = []; let t = LEAD;
lines.forEach((l, i) => {
  const f = path.join(work, `audio/vo/${i}.mp3`), w = path.join(work, `audio/vo/${i}.wav`);
  for (let k = 0; k < 15 && (!fs.existsSync(f) || fs.statSync(f).size < 2000); k++) {
    try { sh("edge-tts", ["--voice", VOICE, "--rate=" + RATE, "--text", l, "--write-media", f], { timeout: 40000 }); }
    catch (e) { Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 3000); }
  }
  if (!fs.existsSync(f) || fs.statSync(f).size < 2000) throw new Error("edge-tts gagal: " + l);
  const tr = "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.03";
  sh("ffmpeg", ["-v", "error", "-y", "-i", f, "-af", `${tr},areverse,${tr},areverse`, "-ar", "44100", "-ac", "2", w]);
  const d = +sh("ffprobe", ["-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", w]);
  if (i === lines.length - 1) t += GAP_CTA - GAP;
  S.push(+t.toFixed(3)); D.push(+d.toFixed(3)); t += d + GAP;
});
{
  const ins = [], fl = [];
  lines.forEach((_, i) => { ins.push("-i", path.join(work, `audio/vo/${i}.wav`)); fl.push(`[${i}]adelay=${Math.round(S[i] * 1000)}:all=1[a${i}]`); });
  sh("ffmpeg", ["-v", "error", "-y", ...ins, "-filter_complex", fl.join(";") + ";" + lines.map((_, i) => `[a${i}]`).join("") + `amix=inputs=${lines.length}:normalize=0,loudnorm=I=-16:TP=-1.5[o]`, "-map", "[o]", "-ar", "44100", "-ac", "2", path.join(work, "audio/vo.wav")]);
}

// ---------- timing ----------
const n = spec.adegan.length;
const T = { sc: spec.adegan.map((_, i) => +(i === 0 ? 0.1 : S[i] - 0.3).toFixed(3)), cta: +(S[n] - 0.35).toFixed(3) };
T.logo = +(S[n] + D[n] + 0.4).toFixed(3);
T.end = +(T.logo + 3.0).toFixed(2);
T.ev = T.sc.map((s, i) => +(s + Math.min(1.1, ((i < n - 1 ? T.sc[i + 1] : T.cta) - s) * 0.35)).toFixed(3));

// ---------- adegan ----------
const KARTU_HITAM = new Set(["angka"]);
function kartu(a, i) {
  const v = a.visual || { jenis: "akuarium" }, id = "v" + i;
  switch (v.jenis) {
    case "angka":
      return `<div class="card black"><svg id="${id}" viewBox="0 0 920 800">
        <text id="num${i}" x="460" y="440" text-anchor="middle" font-size="300" font-weight="700" fill="#fff" letter-spacing="-12">0</text>
        <line id="ln${i}" x1="260" y1="520" x2="660" y2="520" stroke="#8a0a0e" stroke-width="10" pathLength="1"/>
        <text x="460" y="620" text-anchor="middle" font-size="56" fill="#fff">${esc(v.label || "")}</text></svg></div>`;
    case "daftar":
      return `<div class="card"><svg id="${id}" viewBox="0 0 920 800">` + (v.poin || []).slice(0, 3).map((p, k) =>
        `<g id="it${i}_${k}"><circle cx="130" cy="${190 + k * 210}" r="52" fill="#8a0a0e"/>
         <path d="M104 ${190 + k * 210} L124 ${212 + k * 210} L160 ${170 + k * 210}" stroke="#fff" stroke-width="12" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
         <text x="220" y="${208 + k * 210}" font-size="54" font-weight="700" fill="#0b0b0b">${esc(p)}</text></g>`).join("") + `</svg></div>`;
    default: // akuarium, benar, salah
      return `<div class="card"><svg id="${id}" viewBox="0 0 920 800"></svg></div>`;
  }
}
const scenesHtml = spec.adegan.map((a, i) => `
        <div class="sc" id="s${i}">
          <div class="hl" id="h${i}" data-text="${esc(a.headline)}"></div>
          ${kartu(a, i)}
        </div>`).join("");

const SPEC = spec.adegan.map((a) => ({ jenis: (a.visual || {}).jenis || "akuarium", angka: (a.visual || {}).angka || "", satuan: (a.visual || {}).satuan || "", poin: ((a.visual || {}).poin || []).length }));
fs.writeFileSync(path.join(work, "timing.js"), `var VO = ${JSON.stringify({ S, D })};\nvar T = ${JSON.stringify(T)};\nvar SPEC = ${JSON.stringify(SPEC)};\n`);

const html = `<!doctype html>
<html lang="id">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <script src="timing.js"></script>
    <link rel="stylesheet" href="edu.css" />
    <style>#end{background:${B.endBg}} #tagline{color:${B.endInk}} #rule{background:${B.endInk};opacity:.6}</style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="${T.end}" data-width="1080" data-height="1920">
      <audio id="mix" src="audio/mix.wav" data-start="0" data-duration="${T.end}" data-track-index="10" data-volume="1"></audio>
      <video id="bgV" class="bgv" src="clips/bg.mp4" muted playsinline data-start="0" data-duration="${T.cta}" data-media-start="0" data-track-index="2"></video>
      <div id="tint"></div>
      <div id="stage">${scenesHtml}
      </div>
      <div id="vig"></div>
      <div id="cta">
        <video id="ctaV" class="bgv" src="clips/cta.mp4" muted playsinline data-start="${T.cta}" data-duration="${+(T.logo - T.cta).toFixed(3)}" data-media-start="0.5" data-track-index="3"></video>
        <div id="ctaTint"></div>
        <div id="ctaLine"></div>
        <div id="ctaT" data-text="${esc(spec.cta_teks)}"></div>
      </div>
      <div id="end">
        <img id="logo" src="img/logo.png" alt="" />
        <div id="rule"></div>
        <div id="tagline">${esc(B.tagline)}</div>
      </div>
    </div>
    <script src="edu.js"></script>
    <script>
      const CHECK = "M250 430 L400 580 L690 270";
      const tankScenes = [];
      SPEC.forEach((s, i) => {
        if (s.jenis === "akuarium" || s.jenis === "benar" || s.jenis === "salah") {
          tank("v" + i, "t" + i, 110, 150, 700, 470);
          for (let k = 0; k < 3; k++) $("t" + i + "F").insertAdjacentHTML("beforeend", fishMarkup("t" + i + "f" + k, 1));
          tankScenes.push({ i, bub: bubbles("t" + i, 10, i * 30 + 1) });
          if (s.jenis === "salah") {
            $("v" + i).insertAdjacentHTML("beforeend", '<path id="xa' + i + '" pathLength="1" d="M150 190 L770 640" stroke="#8a0a0e" stroke-width="42" stroke-linecap="round" fill="none"/><path id="xb' + i + '" pathLength="1" d="M770 190 L150 640" stroke="#8a0a0e" stroke-width="42" stroke-linecap="round" fill="none"/>');
          }
          if (s.jenis === "benar") {
            $("v" + i).insertAdjacentHTML("beforeend", '<circle id="cb' + i + '" cx="470" cy="420" r="230" fill="#fff" fill-opacity=".9"/><path id="ck' + i + '" pathLength="1" d="' + CHECK + '" stroke="#8a0a0e" stroke-width="46" stroke-linecap="round" stroke-linejoin="round" fill="none"/>');
          }
        }
      });
      function swim(k, n, t, top) {
        const K = TANKS[k], bottom = K.y + K.h - 70;
        for (let i = 0; i < n; i++) {
          const ph = rnd(i + 3) * 6, sp = 0.5 + rnd(i + 8) * 0.3;
          const u = Math.sin(t * sp + ph), x = K.x + K.w / 2 + u * (K.w / 2 - 90);
          const lo = top + 50, y = lo + (0.25 + 0.5 * rnd(i + 13)) * Math.max(0, bottom - lo) + Math.sin(t * 1.7 + ph) * 10;
          setFish(k + "f" + i, x, Math.max(lo, y), Math.sin(t * 2 + ph) * 5, Math.cos(t * sp + ph) < 0);
        }
      }
      function live(t) {
        tankScenes.forEach(({ i, bub }) => { const top = setLevel("t" + i, 0.78); swim("t" + i, 3, t, top); bub(t, 700, 40, top, true); });
        SPEC.forEach((s, i) => {
          if (s.jenis !== "angka") return;
          const target = parseFloat(String(s.angka).replace(",", "."));
          const p = outCubic((t - T.ev[i]) / 1.1);
          $("num" + i).textContent = isNaN(target) ? s.angka + s.satuan : (Number.isInteger(target) ? Math.round(target * p) : (target * p).toFixed(1)) + s.satuan;
        });
      }
      function build() {
        scenes(SPEC.map((_, i) => "s" + i));
        SPEC.forEach((s, i) => {
          words("h" + i, T.sc[i] + (i ? 0.25 : 0.05));
          if (s.jenis === "salah") { draw("#xa" + i, T.ev[i], 0.22, "power3.out"); draw("#xb" + i, T.ev[i] + 0.16, 0.22, "power3.out");
            tl.fromTo("#s" + i + " .card", { x: 0 }, { x: 18, duration: 0.05, yoyo: true, repeat: 5, ease: "none", immediateRender: false }, T.ev[i] + 0.05); }
          if (s.jenis === "benar") { pop("#cb" + i, T.ev[i] - 0.1, "470px 420px"); draw("#ck" + i, T.ev[i] + 0.15, 0.35, "power3.out"); }
          if (s.jenis === "angka") draw("#ln" + i, T.ev[i] + 0.8, 0.4, "expo.out");
          if (s.jenis === "daftar") for (let k = 0; k < s.poin; k++) {
            gsap.set("#it" + i + "_" + k, { opacity: 0, x: -60 });
            tl.to("#it" + i + "_" + k, { opacity: 1, x: 0, duration: 0.4, ease: "expo.out" }, T.ev[i] + k * 0.45);
          }
        });
        ending();
        finish(live);
      }
      document.fonts.ready.then(build);
    </script>
  </body>
</html>
`;
fs.writeFileSync(path.join(work, "index.html"), html);
fs.writeFileSync(path.join(work, "hyperframes.json"), JSON.stringify({ paths: { blocks: "compositions", components: "compositions/components", assets: "assets" }, media: { autoProxy: true } }, null, 2));
fs.writeFileSync(path.join(work, "meta.json"), JSON.stringify({ id: "edukasi", name: "edukasi" }));

// ---------- SFX + musik ----------
const cues = [];
T.sc.forEach((s, i) => { if (i) cues.push(["click", s - 0.05, 0.16, 0.9]); cues.push(["thump", s + 0.05, 0.14]); });
SPEC.forEach((s, i) => {
  const e = T.ev[i];
  if (s.jenis === "salah") cues.push(["wood", e, 0.26, 0.75], ["wood", e + 0.2, 0.4, 0.8]);
  if (s.jenis === "benar") cues.push(["pop5", e + 0.15, 0.5, 1.0]);
  if (s.jenis === "angka") { for (let k = 0; k < 10; k++) cues.push(["tic", e + k * 0.11, 0.5, 1.2]); cues.push(["wood", e + 1.1, 0.5, 1.1]); }
  if (s.jenis === "daftar") for (let k = 0; k < s.poin; k++) cues.push(["pop5", e + k * 0.45, 0.4, 0.9 + k * 0.08]);
});
cues.push(["click", T.cta + 0.1, 0.16, 0.9], ["wood", T.logo, 0.26, 0.75], ["wood", T.logo + 0.45, 0.4, 0.7]);
fs.writeFileSync(path.join(work, "cues.json"), JSON.stringify({ end: T.end, cues }));
sh("node", [path.join(HERE, "mix.cjs"), work, path.join(REPO, "aset/musik", spec.musik)]);

// ---------- render ----------
sh("npx", ["--yes", "hyperframes@0.9.8", "render", work, "-o", path.resolve(output), "--quality", "standard", "--quiet"], { stdio: "inherit", shell: process.platform === "win32" });
console.log(JSON.stringify({ ok: true, durasi: T.end, output }));
