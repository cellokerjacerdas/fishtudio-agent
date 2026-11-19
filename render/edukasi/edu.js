// Mesin video edukasi 20 detik: adegan kartu 3D, headline per kata, ending CTA + logo + tagline.
// Waktu dari T (didefinisikan di timing.js). Semua nilai hidup dihitung dari t lewat live(t), aman saat seek.
window.__timelines = window.__timelines || {};
const tl = gsap.timeline({ paused: true });
const $ = (id) => document.getElementById(id);
const clamp = (v) => Math.max(0, Math.min(1, v));
const rnd = (s) => { const x = Math.sin(s * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
const outCubic = (p) => 1 - Math.pow(1 - clamp(p), 3);
const smooth = (p) => { p = clamp(p); return p * p * (3 - 2 * p); };
const NS = "http://www.w3.org/2000/svg";

// Headline: teks dari data-text, frasa kunci di dalam [ ] dapat blok putih.
function words(id, at, step) {
  const el = $(id), src = el.dataset.text; el.innerHTML = "";
  const spans = [];
  src.split(/(\[[^\]]+\])/).filter(Boolean).forEach((p) => {
    const key = p[0] === "[";
    const chunks = key ? [p.slice(1, -1)] : p.split(/(\s+)/);
    chunks.forEach((w) => {
      if (!w) return;
      if (/^\s+$/.test(w)) { el.appendChild(document.createTextNode(" ")); return; }
      const s = document.createElement("span"); s.className = "wd" + (key ? " k" : "");
      s.innerHTML = (key ? "<i></i>" : "") + "<b>" + w + "</b>"; el.appendChild(s); spans.push(s);
    });
  });
  const st = step || 0.075;
  spans.forEach((s, i) => {
    const b = s.querySelector("b"), bg = s.querySelector("i");
    gsap.set(b, { yPercent: 115 });
    tl.to(b, { yPercent: 0, duration: 0.42, ease: "power4.out" }, at + i * st);
    if (bg) { gsap.set(bg, { scaleX: 0 }); tl.to(bg, { scaleX: 1, duration: 0.32, ease: "power3.out" }, at + i * st + 0.14); }
  });
  return spans;
}

// Adegan masuk dari bawah dengan miring 3D + blur, keluar ke atas.
function scenes(ids) {
  ids.forEach((id, i) => {
    const at = T.sc[i], out = i < ids.length - 1 ? T.sc[i + 1] : T.cta;
    const el = "#" + id;
    tl.fromTo(el, { opacity: 0, y: 260, rotationX: 30, rotationZ: i % 2 ? 3 : -3, scale: 0.88, filter: "blur(16px)" },
      { opacity: 1, y: 0, rotationX: 0, rotationZ: 0, scale: 1, filter: "blur(0px)", duration: 0.55, ease: "expo.out", immediateRender: false }, at);
    tl.to(el, { scale: 1.04, duration: out - at - 0.9, ease: "none" }, at + 0.56);
    tl.to(el, { opacity: 0, y: -260, rotationX: -26, scale: 0.94, filter: "blur(16px)", duration: 0.3, ease: "power3.in" }, out - 0.3);
    const card = document.querySelector(el + " .card");
    if (card) tl.fromTo(card, { rotationY: i % 2 ? -14 : 14, rotationX: 10 }, { rotationY: i % 2 ? 4 : -4, rotationX: 3, duration: out - at, ease: "power2.out", immediateRender: false }, at);
  });
}

function ending() {
  const spans = words("ctaT", T.cta + 0.25, 0.09);
  tl.set("#cta", { opacity: 1 }, T.cta);
  tl.fromTo("#cta", { clipPath: "inset(100% 0% 0% 0%)" }, { clipPath: "inset(0% 0% 0% 0%)", duration: 0.45, ease: "expo.inOut", immediateRender: false }, T.cta - 0.1);
  gsap.set("#ctaLine", { scaleX: 0 });
  tl.to("#ctaLine", { scaleX: 1, duration: 0.5, ease: "expo.out" }, T.cta + 0.2);
  tl.fromTo("#ctaV", { scale: 1.18 }, { scale: 1, duration: T.logo - T.cta, ease: "none", immediateRender: false }, T.cta);
  // Logo
  tl.set("#end", { opacity: 1 }, T.logo);
  tl.fromTo("#logo", { scale: 0.9, opacity: 0, filter: "blur(10px)" }, { scale: 1, opacity: 1, filter: "blur(0px)", duration: 0.7, ease: "expo.out", immediateRender: false }, T.logo);
  gsap.set("#rule", { scaleX: 0 });
  tl.to("#rule", { scaleX: 1, duration: 0.5, ease: "expo.out" }, T.logo + 0.45);
  const tg = $("tagline"), txt = tg.textContent; tg.textContent = "";
  const ch = [...txt].map((c) => { const s = document.createElement("span"); s.textContent = c; s.style.opacity = 0; tg.appendChild(s); return s; });
  tl.to(ch, { opacity: 1, duration: 0.01, stagger: 0.022, ease: "none" }, T.logo + 0.6);
  tl.to("#logo", { scale: 1.03, duration: T.end - T.logo - 0.7, ease: "none" }, T.logo + 0.7);
  return spans;
}

// Gambar garis (path/line dengan pathLength=1)
function draw(sel, at, dur, ease) {
  gsap.set(sel, { strokeDasharray: 1, strokeDashoffset: 1 });
  tl.to(sel, { strokeDashoffset: 0, duration: dur || 0.4, ease: ease || "power2.inOut" }, at);
}
function pop(sel, at, origin) {
  gsap.set(sel, { scale: 0, transformOrigin: origin || "50% 50%" });
  tl.to(sel, { scale: 1, duration: 0.4, ease: "back.out(2.4)" }, at);
}

// Ikan mas koki SVG menghadap kanan, titik tengah di badan.
function fishMarkup(id, s) {
  return '<g id="' + id + '"><g transform="scale(' + s + ')">' +
    '<path d="M-30 0 C-56 -34 -86 -38 -92 -10 C-76 -2 -76 2 -92 12 C-86 38 -56 34 -30 0Z" fill="#5c0407"/>' +
    '<path d="M-10 -26 C-2 -50 16 -44 18 -24Z" fill="#5c0407"/>' +
    '<ellipse cx="0" cy="0" rx="40" ry="30" fill="#8a0a0e"/>' +
    '<circle cx="24" cy="-18" r="15" fill="#8a0a0e"/>' +
    '<circle cx="27" cy="-3" r="6" fill="#fff"/><circle cx="28.5" cy="-3" r="3" fill="#0b0b0b"/>' +
    "</g></g>";
}
function setFish(id, x, y, rot, flip) {
  const e = $(id); if (!e) return;
  e.setAttribute("transform", "translate(" + x.toFixed(1) + " " + y.toFixed(1) + ") rotate(" + (rot || 0).toFixed(2) + ")" + (flip ? " scale(-1 1)" : ""));
}

// Akuarium kaca kotak. Level air diatur setLevel(id, 0..1).
function tankMarkup(id, x, y, w, h) {
  let gravel = "";
  for (let i = 0; i < 26; i++) gravel += '<ellipse cx="' + (x + 14 + (i * (w - 28)) / 25) + '" cy="' + (y + h - 14 - rnd(i + 3) * 10) + '" rx="' + (12 + rnd(i) * 10) + '" ry="' + (8 + rnd(i + 9) * 5) + '" fill="#0b0b0b"/>';
  return '<g id="' + id + '">' +
    '<defs><clipPath id="' + id + 'C"><rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '" rx="10"/></clipPath></defs>' +
    '<g clip-path="url(#' + id + 'C)">' +
    '<rect id="' + id + 'W" x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '" fill="#8a0a0e" fill-opacity=".13"/>' +
    '<rect id="' + id + 'L" x="' + x + '" y="' + y + '" width="' + w + '" height="6" fill="#8a0a0e" fill-opacity=".55"/>' +
    '<g id="' + id + 'X"></g>' + gravel + '<g id="' + id + 'F"></g><g id="' + id + 'B"></g>' +
    "</g>" +
    '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '" rx="10" fill="none" stroke="#0b0b0b" stroke-width="9"/>' +
    '<rect x="' + (x - 14) + '" y="' + (y - 16) + '" width="' + (w + 28) + '" height="22" rx="5" fill="#0b0b0b"/>' +
    "</g>";
}
const TANKS = {};
function tank(svgId, id, x, y, w, h) {
  $(svgId).insertAdjacentHTML("beforeend", tankMarkup(id, x, y, w, h));
  TANKS[id] = { x, y, w, h };
}
function setLevel(id, lv) {
  const k = TANKS[id], top = k.y + k.h * (1 - lv);
  $(id + "W").setAttribute("y", top); $(id + "W").setAttribute("height", k.h * lv + 2);
  $(id + "L").setAttribute("y", top - 3); $(id + "L").style.opacity = lv > 0.02 ? 1 : 0;
  return top;
}
// Gelembung naik dari titik (x0, dasar) sampai permukaan.
function bubbles(id, n, seed) {
  const g = $(id + "B"), bs = [];
  for (let i = 0; i < n; i++) {
    const c = document.createElementNS(NS, "circle");
    c.setAttribute("r", 5 + rnd(seed + i) * 9); c.setAttribute("fill", "none"); c.setAttribute("stroke", "#8a0a0e"); c.setAttribute("stroke-width", 3);
    g.appendChild(c); bs.push({ c, ph: rnd(seed + i + 40), sp: 120 + rnd(seed + i + 80) * 120, dx: rnd(seed + i + 120) });
  }
  return (t, x0, spread, top, on) => {
    const k = TANKS[id], bottom = k.y + k.h - 30;
    bs.forEach((b) => {
      const span = bottom - top; if (!on || span < 40) { b.c.style.opacity = 0; return; }
      const yy = bottom - (((t * b.sp) / span + b.ph) % 1) * span;
      b.c.setAttribute("cx", x0 + (b.dx - 0.5) * spread + Math.sin(t * 3 + b.ph * 9) * 8); b.c.setAttribute("cy", yy);
      b.c.style.opacity = clamp((yy - top) / 30) * 0.9;
    });
  };
}

function finish(live) {
  const clock = { t: 0 };
  tl.fromTo(clock, { t: 0 }, { t: T.end, duration: T.end, ease: "none", onUpdate: () => live(clock.t) }, 0);
  live(0);
  window.__timelines["main"] = tl;
  tl.seek(0);
}
