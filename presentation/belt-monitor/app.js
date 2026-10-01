"use strict";
/* REEFPRINT Live (belt-monitor v3). Plan: PLAN-live-v6.md (ClauDex: Codex gpt-6-astra, 3 rounds, APPROVED).
   Every number shown is read from files produced by code in training/. The assistant only routes to tools;
   answers are rendered by templates from deterministic tool output. */
const P = new URLSearchParams(location.search);
const $ = id => document.getElementById(id);
const css = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const SVGNS = "http://www.w3.org/2000/svg";
function el(t, a = {}, txt) { const e = document.createElementNS(SVGNS, t); for (const k in a) e.setAttribute(k, a[k]); if (txt != null) e.textContent = txt; return e; }
function esc(s) { return String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])); }
const NICE = { "Cu rec": "Cu recovery", "Mo rec": "Mo recovery", "Lime cons": "Lime consumption", "PH": "Flotation pH", "WI": "Bond work index",
  "Pt_ICP_ppm": "Pt", "Pd_ICP_ppm": "Pd", "Rh_ICP_ppm": "Rh", "4E_ppm": "4E (Pt+Pd+Rh+Au)", "Muscovite/Sericite": "Sericite", "Anhydrite/Gypsum": "Anhydrite / gypsum", "Chalcosite/Digenite": "Chalcocite / digenite", "Covelite": "Covellite" };
const UNIT = { "Cu rec": "%", "Mo rec": "%", "Lime cons": "kg/t", "PH": "", "WI": "kWh/t" };
const nice = k => NICE[k] || k.replace(/_/g, " ");
const unit = (rec, k) => rec === "GEOMET" ? (UNIT[k] ?? "") : rec === "MINERAL1" ? "wt%" : "g/t";
function fmt(v, d) { if (v == null || !isFinite(v)) return "∞"; const a = Math.abs(v); d = d ?? (a >= 100 ? 0 : a >= 10 ? 1 : a >= 1 ? 2 : 3); return v.toFixed(d); }
const S = { rec: "GEOMET", headers: { GEOMET: {}, MINERAL1: {} }, cur: null, cube: null, sensor: "vnir_low", layer: "rgb", mode: "2d", running: false,
  scanRow: 0, scanning: false, decided: {}, audit: [], imported: null, ranges: {}, bvIdx: 0, bvTimer: null, plIdx: 0, plTimer: null, plH: "1", plant: {} };

/* ---------------- theme + views ---------------- */
function setTheme(t) { document.documentElement.dataset.reefTheme = t; document.querySelectorAll("#themes button").forEach(b => b.classList.toggle("sel", b.dataset.theme === t)); try { localStorage.setItem("reef-live-theme", t); } catch (e) {} redrawAll(); }
document.querySelectorAll("#themes button").forEach(b => b.onclick = () => setTheme(b.dataset.theme));
const VIEWS = {
  live: ["Track 1 · Belt", "Live scan: see the ore, then decide", "A real hyperspectral scan builds up line by line. Absorption maps show what the camera sees; the model predicts with an honest interval; the policy decides."],
  bushveld: ["Track 4 · Bushveld chromitite (South Africa)", "Belt chemistry to PGE grade", "What a cross-belt XRF / PGNAA-type reading of Cr₂O₃, FeO, SiO₂, MgO, Al₂O₃, CaO can say about Pt, Rh and 4E, held out by project."],
  plant: ["Track 3 · Plant", "Real plant parameters, real forecast, honest result", "A real flotation plant's tags and lab assays, replayed hour by hour with the leakage traps closed."],
  lab: ["Integration", "Lab round trip and exports", "Import QEMSCAN, XRF, XRD or assay results against a typed registry, reconcile, and export to LIMS, historian and GIS."],
  evidence: ["Evidence", "The scoreboard, including what failed", "Every model against its strongest baseline, the previous version and a cheaper camera, with intervals and corrections."],
  where: ["Design", "Where it sits, who uses it, how the models are orchestrated", "Three instruments, three speeds, one decision screen; one router, one referee, one policy."] };
function showView(v) {
  document.querySelectorAll("nav.tabs button").forEach(b => b.classList.toggle("active", b.dataset.view === v));
  document.querySelectorAll(".view").forEach(s => s.classList.toggle("on", s.id === "v-" + v));
  const t = VIEWS[v]; $("crumb").textContent = t[0]; $("title").textContent = t[1]; $("subtitle").textContent = t[2];
  if (v === "bushveld") drawBushveld(); if (v === "plant") drawPlant();
}
document.querySelectorAll("nav.tabs button").forEach(b => b.onclick = () => showView(b.dataset.view));

/* ---------------- audit ---------------- */
function audit(event, data) {
  const e = { ts: new Date().toISOString(), event, ...data, model_sha256: S.summary ? S.summary.hashes_sha256.v6_results.slice(0, 16) : null, policy: S.summary ? S.summary.policy.version : null };
  S.audit.unshift(e);
  $("audit").innerHTML = S.audit.slice(0, 120).map(a => `<div>${esc(a.ts.slice(11, 19))} · ${esc(a.event)} · ${esc(a.sample || a.detail || "")} ${a.decision ? "· " + esc(a.decision) : ""}</div>`).join("");
}
function download(name, text, type) { const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([text], { type: type || "text/plain" })); a.download = name; a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 2000); }
$("auditDl").onclick = () => { download("reefprint_audit.jsonl", S.audit.slice().reverse().map(a => JSON.stringify(a)).join("\n"), "application/x-ndjson"); audit("export", { detail: "audit JSONL" }); };

/* ---------------- cube loading ---------------- */
async function loadCube(rec, s) {
  const h = S.headers[rec][s];
  const buf = new Uint8Array(await fetch(`live/showcase/${rec}/${s}.bin.gz`).then(r => r.arrayBuffer()));
  let raw = buf.buffer;
  if (buf[0] === 0x1f && buf[1] === 0x8b) {
    if (!("DecompressionStream" in window)) throw new Error("This browser cannot decompress the scan data.");
    raw = await new Response(new Blob([buf]).stream().pipeThrough(new DecompressionStream("gzip"))).arrayBuffer();
  }
  const out = {};
  for (const [name, m] of Object.entries(h.arrays)) {
    const C = m.dtype === "uint16" ? Uint16Array : Uint8Array, n = m.shape.reduce((a, b) => a * b, 1);
    out[name] = { data: new C(raw.slice(m.offset, m.offset + n * C.BYTES_PER_ELEMENT)), shape: m.shape, scale: m.scale };
  }
  return out;
}

/* ---------------- colour ---------------- */
const VIR = [[68, 1, 84], [59, 82, 139], [33, 145, 140], [94, 201, 98], [253, 231, 37]];
function cmap(t, stops = VIR) { t = Math.max(0, Math.min(1, t)); const x = t * (stops.length - 1), i = Math.min(stops.length - 2, Math.floor(x)), f = x - i; return stops[i].map((a, j) => Math.round(a + (stops[i + 1][j] - a) * f)); }
const CLU = [[230, 159, 0], [86, 180, 233], [0, 158, 115], [240, 228, 66], [0, 114, 178], [213, 94, 0], [204, 121, 167], [153, 153, 153], [166, 86, 40], [102, 194, 165], [141, 160, 203], [231, 138, 195]];
const LAYERS = { vnir_low: [["rgb", "False colour"], ["map_vnir_fe3", "Fe³⁺ ~0.9 µm"], ["clusters", "Clusters"]],
  swir_low: [["rgb", "False colour"], ["map_swir_aloh", "Al-OH ~2.2 µm"], ["map_swir_mgoh", "Mg-OH/CO₃ ~2.33 µm"], ["map_swir_h2o", "H₂O ~1.9 µm"], ["clusters", "Clusters"]] };
const LAYER_NOTE = { map_vnir_fe3: "band depth at ~900 nm (ferric iron)", map_swir_aloh: "band depth at ~2205 nm (sericite, kaolinite)", map_swir_mgoh: "band depth at ~2330 nm (chlorite, biotite, talc, carbonate)", map_swir_h2o: "band depth at ~1910 nm (water)", clusters: "k-means clusters of spectral shape (training-fold fit)" };
function layerButtons() {
  $("layerSel").innerHTML = LAYERS[S.sensor].map(([k, n]) => `<button data-l="${k}" class="${k === S.layer ? "sel" : ""}">${n}</button>`).join("");
  $("layerSel").querySelectorAll("button").forEach(b => b.onclick = () => { S.layer = b.dataset.l; layerButtons(); paint(); });
}
function imageFor(sensor, layer) {
  const c = S.cube; if (!c) return null;
  const cube = c[sensor + "_cube"]; if (!cube) return null;
  const [h, w, B] = cube.shape, d = cube.data, img = new Uint8ClampedArray(h * w * 4), dark = c[sensor + "_dark"].data;
  const hd = S.headers[S.rec][S.cur], wl = hd[sensor + "_wavelengths"];
  const near = x => wl.reduce((bi, v, i) => Math.abs(v - x) < Math.abs(wl[bi] - x) ? i : bi, 0);
  if (layer === "rgb") {
    const bands = sensor === "vnir_low" ? [near(640), near(550), near(460)] : [near(2200), near(1650), near(1300)];
    const lim = bands.map(b => { const v = []; for (let i = 0; i < h * w; i += 3) v.push(d[i * B + b]); v.sort((a, b2) => a - b2); return [v[Math.floor(v.length * .02)], v[Math.floor(v.length * .98)] || 1]; });
    for (let i = 0; i < h * w; i++) for (let k = 0; k < 3; k++) { const [lo, hi] = lim[k]; img[i * 4 + k] = 255 * Math.max(0, Math.min(1, (d[i * B + bands[k]] - lo) / Math.max(1, hi - lo))); img[i * 4 + 3] = 255; }
    return { img, w, h };
  }
  if (layer === "clusters") { const L = c[sensor + "_clusters"].data; for (let i = 0; i < h * w; i++) { const col = dark[i] ? [40, 40, 40] : CLU[L[i] % CLU.length]; img.set([...col, 255], i * 4); } return { img, w, h }; }
  const m = c[layer]; if (!m) return null;
  for (let i = 0; i < h * w; i++) { const col = dark[i] ? [35, 35, 35] : cmap(m.data[i] / 255); img.set([...col, 255], i * 4); }
  return { img, w, h, scale: m.scale };
}

/* ---------------- painting the scan ---------------- */
let raf = 0;
function paint() {
  const r = imageFor(S.sensor, S.layer), cv = $("scan");
  if (!r) return;
  cv.width = r.w; cv.height = r.h;
  const wrap = $("scanwrap").getBoundingClientRect(), k = Math.min((wrap.width - 20) / r.w, (wrap.height - 20) / r.h);
  cv.style.width = Math.round(r.w * k) + "px"; cv.style.height = Math.round(r.h * k) + "px";
  const ctx = cv.getContext("2d"), id = ctx.createImageData(r.w, r.h), rows = Math.min(r.h, Math.ceil(S.scanRow * r.h));
  for (let i = 0; i < rows * r.w * 4; i++) id.data[i] = r.img[i];
  for (let i = rows * r.w * 4; i < r.h * r.w * 4; i += 4) { id.data[i] = 13; id.data[i + 1] = 23; id.data[i + 2] = 32; id.data[i + 3] = 255; }
  ctx.putImageData(id, 0, 0);
  const sl = $("scanline"), cr = cv.getBoundingClientRect(), wr = $("scanwrap").getBoundingClientRect();
  if (S.scanning) { sl.style.display = "block"; sl.style.top = (cr.top - wr.top + rows / r.h * cr.height) + "px"; } else sl.style.display = "none";
  const lb = $("legendbar");
  if (r.scale && Array.isArray(r.scale)) { lb.style.display = "block"; $("lgTitle").textContent = (LAYER_NOTE[S.layer] || "") + (r.scale[1] <= 0 ? " · all values ≤ 0: no detectable absorption here; along-track stripes are likely detector pattern, not mineralogy" : ""); $("lgMin").textContent = r.scale[0].toFixed(3); $("lgMax").textContent = r.scale[1].toFixed(3);
    const g = $("lgBar").getContext("2d"); for (let x = 0; x < 180; x++) { g.fillStyle = `rgb(${cmap(x / 179).join(",")})`; g.fillRect(x, 0, 1, 9); } }
  else if (S.layer === "clusters") { lb.style.display = "block"; $("lgTitle").textContent = LAYER_NOTE.clusters; $("lgMin").textContent = ""; $("lgMax").textContent = ""; const g = $("lgBar").getContext("2d"); for (let x = 0; x < 12; x++) { g.fillStyle = `rgb(${CLU[x].join(",")})`; g.fillRect(x * 15, 0, 15, 9); } }
  else lb.style.display = "none";
  const hd = S.headers[S.rec][S.cur];
  $("hud").innerHTML = `${esc(S.cur)} · ${S.sensor === "vnir_low" ? "VNIR" : "SWIR"} · ${r.w}×${r.h} px · ${S.cube[S.sensor + "_cube"].shape[2]} bands<br>${S.scanning ? "scanning line " + rows + " / " + r.h : "scan complete"}`;
  $("hud2").textContent = S.layer === "rgb" ? (S.sensor === "vnir_low" ? "R 640 · G 550 · B 460 nm" : "R 2200 · G 1650 · B 1300 nm") : (LAYERS[S.sensor].find(l => l[0] === S.layer) || ["", ""])[1];
  if (S.mode === "3d") build3d();
}
function pixelSpectrum(sensor, r, c) { const cube = S.cube[sensor + "_cube"], [h, w, B] = cube.shape, sc = cube.scale; const out = new Array(B); for (let b = 0; b < B; b++) out[b] = cube.data[(r * w + c) * B + b] * sc; return out; }
function meanSpectrum(sensor, rowsFrac) {
  const cube = S.cube[sensor + "_cube"], [h, w, B] = cube.shape, sc = cube.scale, dark = S.cube[sensor + "_dark"].data, rows = Math.max(1, Math.ceil(rowsFrac * h)), out = new Float64Array(B); let n = 0;
  for (let i = 0; i < rows * w; i++) { if (dark[i]) continue; for (let b = 0; b < B; b++) out[b] += cube.data[i * B + b]; n++; }
  return Array.from(out, v => v / Math.max(1, n) * sc);
}
let hover = null;
$("scan").addEventListener("mousemove", e => { if (!S.cube) return; const cv = $("scan"), r = cv.getBoundingClientRect(); const c = Math.floor((e.clientX - r.left) / r.width * cv.width), rr = Math.floor((e.clientY - r.top) / r.height * cv.height); hover = [rr, c]; drawSpec(); });
$("scan").addEventListener("mouseleave", () => { hover = null; drawSpec(); });
function drawSpec() {
  const svg = $("spec"); svg.innerHTML = ""; if (!S.cube || !S.cur) return;
  const hd = S.headers[S.rec][S.cur], W = 900, H = 220, L = 56, R = 12, T = 12, B = 30, mu = css("--muted"), ln = css("--line");
  const x = w => L + (w - 400) / 2100 * (W - L - R);
  const lines = [];
  for (const s of ["vnir_low", "swir_low"]) if (S.cube[s + "_cube"]) lines.push({ s, wl: hd[s + "_wavelengths"], v: meanSpectrum(s, S.scanning ? S.scanRow : 1), dash: "" });
  const hvRow = hover && S.cube[S.sensor + "_cube"] && hover[0] < S.cube[S.sensor + "_cube"].shape[0] && hover[1] < S.cube[S.sensor + "_cube"].shape[1] && hover[0] >= 0 && hover[1] >= 0;
  if (hvRow) lines.push({ s: S.sensor, wl: hd[S.sensor + "_wavelengths"], v: pixelSpectrum(S.sensor, hover[0], hover[1]), dash: "4 3", pix: true });
  const ymax = Math.max(1, ...lines.flatMap(l => l.v)) * 1.05, y = v => T + (1 - v / ymax) * (H - T - B);
  [[1380, 1460, "OH"], [1880, 1960, "H₂O"], [2160, 2230, "Al-OH"], [2300, 2360, "Mg-OH/CO₃"], [860, 960, "Fe³⁺"]].forEach(([a, b, t]) => { svg.appendChild(el("rect", { x: x(a), y: T, width: x(b) - x(a), height: H - T - B, fill: css("--blue-light") })); svg.appendChild(el("text", { x: (x(a) + x(b)) / 2, y: T + 10, "font-size": 10, fill: mu, "text-anchor": "middle" }, t)); });
  for (let k = 0; k <= 4; k++) { const v = ymax * k / 4; svg.appendChild(el("line", { x1: L, x2: W - R, y1: y(v), y2: y(v), stroke: ln })); svg.appendChild(el("text", { x: L - 6, y: y(v) + 4, "font-size": 10, fill: mu, "text-anchor": "end" }, Math.round(v).toLocaleString("en-ZA"))); }
  for (let w = 500; w <= 2500; w += 250) svg.appendChild(el("text", { x: x(w), y: H - 10, "font-size": 10.5, fill: mu, "text-anchor": "middle" }, w));
  lines.forEach(l => { let d = ""; l.wl.forEach((w, j) => d += (d ? "L" : "M") + x(w).toFixed(1) + "," + y(l.v[j]).toFixed(1)); svg.appendChild(el("path", { d, fill: "none", stroke: l.pix ? css("--ink") : css(l.s === "vnir_low" ? "--blue" : "--copper"), "stroke-width": l.pix ? 1.6 : 2.4, "stroke-dasharray": l.dash })); });
  $("specLegend").innerHTML = `<span><i style="background:var(--blue)"></i>VNIR mean of scanned lines</span><span><i style="background:var(--copper)"></i>SWIR mean of scanned lines</span>` + (hvRow ? `<span><i style="background:var(--ink)"></i>pixel (${hover[0]}, ${hover[1]}), ${S.sensor === "vnir_low" ? "VNIR" : "SWIR"} only</span>` : `<span>Hover the image to see a pixel's spectrum. The two cameras are not co-registered, so pixels are never joined across sensors.</span>`) + `<span>Units: sensor units as published</span>`;
}

/* ---------------- 3D data cube (real faces) ---------------- */
let rot = [-24, -38], drag = null;
function faceCanvas(w, h, fill) { const c = document.createElement("canvas"); c.width = w; c.height = h; const g = c.getContext("2d"), id = g.createImageData(w, h); fill(id.data); g.putImageData(id, 0, 0); return c; }
function build3d() {
  const cube = S.cube[S.sensor + "_cube"]; if (!cube) return;
  const [h, w, B] = cube.shape, d = cube.data, r = imageFor(S.sensor, S.layer), rig = $("rig"); rig.innerHTML = "";
  let mx = 1; for (let i = 0; i < d.length; i += 7) mx = Math.max(mx, d[i]);
  const k = Math.min(300 / w, 220 / h), kb = 150 / B, W = w * k, H = h * k, D = B * kb;
  const top = faceCanvas(w, B, a => { for (let b = 0; b < B; b++) for (let x = 0; x < w; x++) { const col = cmap(d[(0 * w + x) * B + b] / mx, [[0, 0, 4], [87, 16, 110], [188, 55, 84], [249, 142, 9], [252, 255, 164]]); a.set([...col, 255], (b * w + x) * 4); } });
  const side = faceCanvas(B, h, a => { for (let yy = 0; yy < h; yy++) for (let b = 0; b < B; b++) { const col = cmap(d[(yy * w + (w - 1)) * B + b] / mx, [[0, 0, 4], [87, 16, 110], [188, 55, 84], [249, 142, 9], [252, 255, 164]]); a.set([...col, 255], (yy * B + b) * 4); } });
  const front = faceCanvas(w, h, a => a.set(r.img));
  const rows = Math.min(h, Math.ceil(S.scanRow * h));
  if (rows < h) { const g = front.getContext("2d"); g.fillStyle = "#0d1720"; g.fillRect(0, rows, w, h - rows); }
  [[front, W, H, ""], [top, W, D, "rotateX(-90deg)"], [side, D, H, `translateX(${W}px) rotateY(90deg)`]].forEach(([c, cw, ch, tf]) => { c.style.width = cw + "px"; c.style.height = ch + "px"; c.style.transform = tf; rig.appendChild(c); });
  rig.style.width = W + "px"; rig.style.height = H + "px";
  rig.style.transform = `translate3d(${-W / 2 + D / 4}px,${-H / 2 + D / 3}px,0) rotateX(${rot[0]}deg) rotateY(${rot[1]}deg)`;
  rig.parentElement.title = "Drag to rotate. Front: the image; top and side: the real spectra of the edge pixels, band by band.";
}
$("cube3d").addEventListener("mousedown", e => drag = [e.clientX, e.clientY, ...rot]);
window.addEventListener("mouseup", () => drag = null);
window.addEventListener("mousemove", e => { if (!drag) return; rot = [Math.max(-80, Math.min(20, drag[2] - (e.clientY - drag[1]) * .4)), drag[3] + (e.clientX - drag[0]) * .4]; if (S.mode === "3d") build3d(); });

/* ---------------- policy (total table, PLAN §E) ---------------- */
function targetState(rec, k, t) {
  const dir = S.summary.policy.adverse[k] || "none";
  if (!isFinite(t.lo) || !isFinite(t.hi)) return { s: "crossing", dir };
  if (dir === "low") { const thr = t.t_low; return { s: t.lo > thr ? "clear" : t.hi <= thr ? "adverse" : "crossing", thr, dir }; }
  if (dir === "high") { const thr = t.t_high; return { s: t.hi < thr ? "clear" : t.lo >= thr ? "adverse" : "crossing", thr, dir }; }
  return { s: "context", dir };
}
function decide(rec, h) {
  const ev = S.summary.evidence[rec], used = Object.keys(h.targets).filter(k => ev[k] && ev[k].used_in_decision), states = {};
  used.forEach(k => states[k] = targetState(rec, k, h.targets[k]));
  const adverse = used.filter(k => states[k].s === "adverse"), crossing = used.filter(k => states[k].s === "crossing"), A = S.summary.policy.actions;
  if (h.ood === "refused") return { code: "default", row: 1, title: "Conservative default: review only", items: ["Spectrum is outside the training domain (OOD above the calibration p99). Route this parcel to the lab or microscope.", "Do not use these predictions for any setpoint."], used, states };
  if (adverse.length >= 2) return { code: "default", row: 2, title: "Conservative default: review only", items: adverse.map(k => `${nice(k)} is adverse: ${A[k]}.`), used, states };
  if (adverse.length === 1) return { code: "verify", row: 3, title: `Verify: ${nice(adverse[0])} beyond its band`, items: [A[adverse[0]] + "."], used, states };
  if (!used.length) return { code: "verify", row: 4, title: "Verify: no validated decision target for this sample type", items: [rec === "MINERAL1" ? "On plant-feed fractions, the spectrum did not add anything beyond the size fraction and process line, so no mineral prediction is used for decisions." : "No target clears the evidence bar.", "Route to the lab or microscope on the normal schedule."], used, states };
  if (crossing.length || h.ood === "borderline") return { code: "verify", row: 4, title: "Verify: the interval crosses a threshold", items: [...crossing.map(k => `${nice(k)}: the 80% interval crosses the ${states[k].dir === "high" ? "upper" : "lower"} band, so it is uncertain which side this parcel is on.`), ...(h.ood === "borderline" ? ["Spectrum is near the edge of the training domain (between p95 and p99)."] : [])], used, states };
  return { code: "act", row: 5, title: "Act: continue at setpoint", items: ["Every decision target is inside its normal band with its whole interval; next microscope check on schedule."], used, states };
}

/* ---------------- live scan flow ---------------- */
function queueItems() { return S.summary.showcase[S.rec]; }
function renderQueue() {
  $("queue").innerHTML = queueItems().map(s => { const h = S.headers[S.rec][s], dcs = S.decided[S.rec + s]; return `<button class="qi ${s === S.cur ? "cur" : ""}" data-s="${esc(s)}"><div><b>${esc(s)}</b><small>${S.rec === "GEOMET" ? "drill core" : esc(h.tags || "plant feed")} · fold ${h.fold + 1} · OOD ${esc(h.ood)}</small></div><span class="st ${dcs ? dcs : "idle"}">${dcs ? (dcs === "default" ? "DEFAULT" : dcs.toUpperCase()) : "queued"}</span></button>`; }).join("");
  $("queue").querySelectorAll(".qi").forEach(b => b.onclick = () => { stopRun(); startScan(b.dataset.s); });
}
function setStep(n) { for (let i = 1; i <= 5; i++) { $("st" + i).classList.toggle("on", i === n); $("st" + i).classList.toggle("done", i < n); } }
async function startScan(s) {
  S.cur = s; S.scanRow = 0; S.scanning = true; S.cube = null; renderQueue(); setStep(1);
  const h = S.headers[S.rec][s];
  $("scanTitle").textContent = `Line scan · ${s}`;
  $("scanSub").textContent = S.rec === "GEOMET" ? "HIDSAG GEOMET drill-core composite · porphyry Cu-Mo, Chile · out-of-fold" : `HIDSAG MINERAL1 plant-feed fraction · ${h.tags} · out-of-fold`;
  $("oodBadge").className = "badge " + (h.ood === "pass" ? "ok" : h.ood === "borderline" ? "warn" : "bad"); $("oodBadge").textContent = "OOD " + h.ood;
  $("preds").innerHTML = `<div class="copy muted">Scanning…</div>`; $("advice").style.display = "none"; $("why").innerHTML = "—";
  audit("scan_start", { record: S.rec, sample: s });
  try { S.cube = await loadCube(S.rec, s); } catch (e) { audit("error", { sample: s, detail: String(e.message || e) }); $("preds").innerHTML = `<div class="copy bad">${esc(e.message || e)}</div>`; return; }
  layerButtons();
  const dur = +(P.get("scan") || 4500), t0 = performance.now();
  cancelAnimationFrame(raf);
  const step = now => { S.scanRow = Math.min(1, (now - t0) / dur); paint(); drawSpec(); if (S.scanRow < 1) raf = requestAnimationFrame(step); else finishScan(); };
  raf = requestAnimationFrame(step);
}
function finishScan() {
  S.scanning = false; paint(); drawSpec(); setStep(2);
  const rec = S.rec, s = S.cur, h = S.headers[rec][s];
  setTimeout(() => { setStep(3); renderPreds(rec, h); }, 450);
  setTimeout(() => {
    setStep(4); const d = decide(rec, h); renderAdvice(d, rec, h); S.decided[rec + s] = d.code; renderQueue();
    setTimeout(() => { setStep(5); audit("decision", { record: rec, sample: s, decision: d.code, policy_row: d.row, ood: h.ood, targets_used: d.used.join(",") }); if (S.running) runTimer = setTimeout(nextScan, +(P.get("dwell") || 3500)); }, 450);
  }, 1000);
}
function rangeOf(rec, k) {
  const key = rec + k; if (S.ranges[key]) return S.ranges[key];
  const v = []; Object.values(S.headers[rec]).forEach(h => { const t = h.targets[k]; if (t) v.push(t.true, t.pred, isFinite(t.lo) ? t.lo : t.pred, isFinite(t.hi) ? t.hi : t.pred, t.t_low, t.t_high); });
  const lo = Math.min(...v), hi = Math.max(...v), pad = (hi - lo) * .05 || 1; return S.ranges[key] = [lo - pad, hi + pad];
}
function predRow(rec, k, t, used, state) {
  const [lo, hi] = rangeOf(rec, k), pos = v => Math.max(0, Math.min(100, (v - lo) / (hi - lo) * 100)), u = unit(rec, k), ev = S.summary.evidence[rec][k] || {};
  const thrs = rec === "GEOMET" && S.summary.policy.adverse[k] !== "none" ? [S.summary.policy.adverse[k] === "low" ? t.t_low : t.t_high] : [];
  const badge = used ? `<span class="badge ${state === "clear" ? "ok" : state === "adverse" ? "bad" : "warn"}">${state}</span>` : `<span class="badge">context only</span>`;
  return `<div class="prow ${used ? "" : "ctx"}"><div class="top"><span class="name">${esc(nice(k))} ${badge}</span><span class="val">${fmt(t.pred)}<small>${esc(u)}</small></span></div>
    <div class="track"><div class="band" style="left:${pos(isFinite(t.lo) ? t.lo : lo)}%;width:${Math.max(1, pos(isFinite(t.hi) ? t.hi : hi) - pos(isFinite(t.lo) ? t.lo : lo))}%"></div>${thrs.map(v => `<div class="tick" style="left:${pos(v)}%"></div>`).join("")}<div class="pt" style="left:${pos(t.pred)}%"></div><div class="lab" style="left:${pos(t.true)}%" title="lab result, revealed later"></div></div>
    <div class="sub"><span>80% interval ${fmt(t.lo)}–${fmt(t.hi)} · lab (revealed later) ${fmt(t.true)}</span><span>${ev.r2_deployable != null ? "R² " + ev.r2_deployable.toFixed(2) : ""}${ev.coverage != null ? " · coverage " + Math.round(ev.coverage * 100) + "%" : ""}</span></div>
    ${!used ? `<div class="sub"><span>${rec === "MINERAL1" ? "Explained by size fraction and process line (a lookup does as well)" : "Did not beat the " + esc(ev.strongest_baseline || "baseline") + " under all gates"}</span></div>` : ""}</div>`;
}
function renderPreds(rec, h) {
  const ev = S.summary.evidence[rec];
  let keys = Object.keys(h.targets);
  if (rec === "MINERAL1") keys = ["Chalcopyrite", "Pyrite", "Bornite", "Molybdenite", "Muscovite/Sericite", "Biotite", "Chlorite", "Quartz"].filter(k => h.targets[k]);
  keys.sort((a, b) => (ev[b] && ev[b].used_in_decision) - (ev[a] && ev[a].used_in_decision));
  const d = decide(rec, h);
  $("preds").innerHTML = keys.map(k => predRow(rec, k, h.targets[k], ev[k] && ev[k].used_in_decision, d.states[k] ? d.states[k].s : "context")).join("") + (rec === "MINERAL1" ? `<div class="copy muted">Showing 8 of ${Object.keys(h.targets).length} minerals.</div>` : "");
  const why = keys.slice(0, rec === "GEOMET" ? 5 : 4).map(k => { const e = h.targets[k].explain; const u = unit(rec, k); return `<p><b>${esc(nice(k))}</b>: ${e.regions.map(r => `${esc(r.region)} (${r.delta >= 0 ? "+" : ""}${fmt(r.delta)} ${esc(u)})`).join(", ")}. <span class="muted">Brightness ablation ${fmt(e.ablation_brightness)}, cluster ablation ${fmt(e.ablation_clusters)}.</span></p>`; }).join("");
  $("why").innerHTML = why + `<p class="muted">Each region of the raw spectrum was replaced by the training mean and every feature recomputed; the number is how far the prediction moved. It is an association with a wavelength region, not a mechanism, and the regions do not add up.</p>`;
  const rr = S.summary.v6_records[rec], fold = rr.calibration[h.fold];
  $("prov").innerHTML = [["Model", "v6 deployable (proper-training), chosen per target by grouped inner CV"], ["Interval", `80% split-conformal · ${fold.n_cal_units} calibration ${rec === "MINERAL1" ? "composites" : "samples"} · k=${fold.k}`], ["Fold", `${h.fold + 1} of 5 (sample never trained on)`], ["OOD", `${h.ood} (calibration p95 / p99 bands)`], ["Results sha256", S.summary.hashes_sha256.v6_results.slice(0, 16) + "…"], ["Policy", S.summary.policy.version]].map(([a, b]) => `<dt>${esc(a)}</dt><dd>${esc(b)}</dd>`).join("");
}
function renderAdvice(d, rec, h) {
  const a = $("advice"); a.style.display = "block";
  a.innerHTML = `<div class="hd"><span class="st ${d.code}">${d.code === "default" ? "CONSERVATIVE DEFAULT" : d.code.toUpperCase()}</span><h3>${esc(d.title)}</h3></div><ul>${d.items.map(i => `<li>${esc(i)}</li>`).join("")}</ul><div class="note">Policy ${esc(S.summary.policy.version)}, row ${d.row} of 5. Decision targets: ${d.used.length ? d.used.map(nice).join(", ") : "none"}. Thresholds: training-fold p25 / p75, illustrative. A conservative default is a reviewed recipe, never "hold the last setpoint".</div>`;
}
let runTimer = 0;
function nextScan() { const q = queueItems(), i = q.indexOf(S.cur); startScan(q[(i + 1) % q.length]); }
function stopRun() { S.running = false; clearTimeout(runTimer); $("runBtn").textContent = "Run belt"; }
$("runBtn").onclick = () => { if (S.running) { stopRun(); return; } S.running = true; $("runBtn").textContent = "Pause belt"; nextScan(); };
$("nextBtn").onclick = () => { stopRun(); nextScan(); };
$("recSel").querySelectorAll("button").forEach(b => b.onclick = () => { stopRun(); S.rec = b.dataset.rec; $("recSel").querySelectorAll("button").forEach(x => x.classList.toggle("sel", x === b)); S.cur = null; startScan(queueItems()[0]); });
$("sensorSel").querySelectorAll("button").forEach(b => b.onclick = () => { S.sensor = b.dataset.s; S.layer = "rgb"; $("sensorSel").querySelectorAll("button").forEach(x => x.classList.toggle("sel", x === b)); layerButtons(); paint(); drawSpec(); });
$("modeSel").querySelectorAll("button").forEach(b => b.onclick = () => { S.mode = b.dataset.m; $("modeSel").querySelectorAll("button").forEach(x => x.classList.toggle("sel", x === b)); $("scanwrap").style.display = S.mode === "2d" ? "flex" : "none"; $("cube3d").style.display = S.mode === "3d" ? "flex" : "none"; paint(); });

/* ---------------- Bushveld ---------------- */
function bvRows() { if (!S.bvOrder) { S.bvOrder = S.bv.rows.map((r, i) => i).sort((a, b) => { const A = S.bv.rows[a], B = S.bv.rows[b]; return A.bh === B.bh ? A.from - B.from : (A.bh < B.bh ? -1 : 1); }); } return S.bvOrder; }
function drawBushveld() {
  if (!S.bv) return;
  const r = S.bv.rows[bvRows()[S.bvIdx % bvRows().length]], beats = S.bv.beats_baseline;
  $("bvSub").textContent = `${r.project} · borehole ${r.bh} · ${r.from.toFixed(2)}–${r.to.toFixed(2)} m`;
  const OXM = { "Cr2O3_%": 55, "FeO_%": 30, "SiO2_%": 40, "MgO_%": 30, "Al2O3_%": 25, "CaO_%": 15 };
  $("oxbars").innerHTML = Object.entries(r.ox).map(([k, v]) => `<div><span>${esc(k.replace("_%", ""))}</span><i style="width:${Math.min(100, v / OXM[k] * 100)}%"></i><span style="text-align:right">${v.toFixed(2)} %</span></div>`).join("");
  $("bvMeta").innerHTML = [["Logged seam", r.seam], ["Predicted seam", `${r.seam_pred} (${Math.round(r.seam_conf * 100)}%)`], ["Fold", `${r.fold + 1} of 5 (project held out)`], ["Source", "Bachmann et al. 2019, CC BY 4.0"]].map(([a, b]) => `<dt>${esc(a)}</dt><dd>${esc(b)}</dd>`).join("");
  const TG = ["4E_ppm", "Pt_ICP_ppm", "Rh_ICP_ppm", "Pd_ICP_ppm"];
  $("bvPreds").innerHTML = TG.map(k => { const t = r.pge[k], used = beats[k], th = r.thr[k], hiV = t.hi == null ? Infinity : t.hi;
    const st = !used ? "context" : (t.lo >= th[1] ? "high" : hiV <= th[0] ? "low" : "crossing");
    const vmax = Math.max(th[1] * 2.2, t.true * 1.1, t.pred * 1.2), pos = v => Math.max(0, Math.min(100, v / vmax * 100));
    return `<div class="prow ${used ? "" : "ctx"}"><div class="top"><span class="name">${esc(nice(k))} ${used ? `<span class="badge ${st === "high" ? "ok" : st === "low" ? "warn" : "warn"}">${st}</span>` : `<span class="badge">context only</span>`}</span><span class="val">${fmt(t.pred)}<small>g/t</small></span></div>
      <div class="track"><div class="band" style="left:${pos(t.lo)}%;width:${Math.max(1, pos(hiV) - pos(t.lo))}%"></div><div class="tick" style="left:${pos(th[0])}%"></div><div class="tick" style="left:${pos(th[1])}%"></div><div class="pt" style="left:${pos(t.pred)}%"></div><div class="lab" style="left:${pos(t.true)}%"></div></div>
      <div class="sub"><span>80% interval ${fmt(t.lo)}–${fmt(t.hi)} · ICP assay (revealed later) ${fmt(t.true)}</span><span>bands p25 ${fmt(th[0])} / p75 ${fmt(th[1])}</span></div>${!used ? `<div class="sub"><span>Did not beat the average guess under all gates</span></div>` : ""}</div>`; }).join("");
  const t4 = r.pge["4E_ppm"], th = r.thr["4E_ppm"], hi4 = t4.hi == null ? Infinity : t4.hi;
  const d = t4.lo >= th[1] ? ["act", "ACT", "PGE-rich parcel: route to the PGM recovery circuit (illustrative)"] : hi4 <= th[0] ? ["act", "ACT", "Low-PGE parcel: chrome-only route is a candidate (illustrative)"] : ["verify", "VERIFY", "Uncertain grade: send for fire assay before routing"];
  $("bvAdvice").innerHTML = `<div class="hd"><span class="st ${d[0]}">${d[1]}</span><h3>${esc(d[2])}</h3></div><ul><li>4E 80% interval ${fmt(t4.lo)}–${fmt(t4.hi)} g/t against training bands ${fmt(th[0])} / ${fmt(th[1])} g/t.</li><li>Seam from chemistry: ${esc(r.seam_pred)} (${Math.round(r.seam_conf * 100)}%); logged: ${esc(r.seam)}.</li></ul><div class="note">Routing labels are illustrative; site cut-offs and plant routes replace them. These are lab assays of drill core standing in for a belt reading.</div>`;
  drawBvLog(r);
  const sm = S.summary.bushveld, row = (k, x) => { const q1 = Object.entries(x).find(([kk]) => kk.startsWith("Q1_")), q2 = x["Q2_chem_plus_seam_vs_seam_only"]; return `<tr><td>${esc(nice(k))}</td><td class="num">${x.r2_chem.toFixed(2)}</td><td class="num">${x.r2_seam_only.toFixed(2)}</td><td class="num">${x.r2_chem_seam.toFixed(2)}</td><td>${esc(q1 ? q1[1].verdict : "")}</td><td>${esc(q2.verdict)} <span class="muted">(paired p ${q2.wilcoxon_p_less_projects.toFixed(3)})</span></td><td class="num">${Math.round(x.coverage_one_per_project * 100)}% [${Math.round(x.coverage_one_per_project_ci95[0] * 100)}–${Math.round(x.coverage_one_per_project_ci95[1] * 100)}]</td></tr>`; };
  $("bvEvidence").innerHTML = `<table><thead><tr><th>Grade (log ppm)</th><th class="num">R² chemistry</th><th class="num">R² seam only</th><th class="num">R² both</th><th>Chemistry vs average</th><th>Chemistry adds to seam?</th><th class="num">Coverage (per project)</th></tr></thead><tbody>${Object.entries(sm.targets).map(([k, x]) => row(k, x)).join("")}</tbody></table><div class="copy muted"><p>Seam from chemistry: balanced accuracy ${(sm.seam.balanced_accuracy * 100).toFixed(0)}% against ${(sm.seam.balanced_accuracy_majority * 100).toFixed(1)}% for the majority class (8 seams, LG6–MG4).</p><p>"Chemistry adds to seam" passes the paired project-level tests for Pt, Rh and 4E but fails the doctrine's unpaired Mann–Whitney gate, so it is reported as no significant difference.</p></div>`;
}
function drawBvLog(cur) {
  const svg = $("bvLog"); svg.innerHTML = ""; const rows = S.bv.rows.filter(r => r.bh === cur.bh).sort((a, b) => a.from - b.from);
  $("bvLogTitle").textContent = `Downhole log · borehole ${cur.bh} (${rows.length} intervals)`;
  const W = 900, H = 360, T = 18, B = 26, d0 = Math.min(...rows.map(r => r.from)), d1 = Math.max(...rows.map(r => r.to)), span = Math.max(d1 - d0, 1);
  const y = d => T + (d - d0) / span * (H - T - B), mu = css("--muted"), ln = css("--line");
  svg.appendChild(el("text", { x: 10, y: 12, "font-size": 10.5, fill: mu }, "depth (m)")); svg.appendChild(el("text", { x: 140, y: 12, "font-size": 10.5, fill: mu }, "seam")); svg.appendChild(el("text", { x: 240, y: 12, "font-size": 10.5, fill: mu }, "Cr₂O₃ %")); svg.appendChild(el("text", { x: 520, y: 12, "font-size": 10.5, fill: mu }, "4E g/t (log scale)"));
  const lx = v => 520 + (Math.log10(Math.max(v, 0.01)) + 2) / 3.3 * 360;
  [0.01, 0.1, 1, 10].forEach(v => { svg.appendChild(el("line", { x1: lx(v), x2: lx(v), y1: T, y2: H - B, stroke: ln })); svg.appendChild(el("text", { x: lx(v), y: H - 8, "font-size": 10, fill: mu, "text-anchor": "middle" }, v)); });
  rows.forEach(r => { const y0 = y(r.from), y1 = Math.max(y(r.to), y0 + 3), isCur = r === cur;
    svg.appendChild(el("text", { x: 10, y: (y0 + y1) / 2 + 4, "font-size": 10, fill: mu }, r.from.toFixed(1)));
    svg.appendChild(el("text", { x: 140, y: (y0 + y1) / 2 + 4, "font-size": 10.5, fill: css("--ink"), "font-weight": isCur ? 700 : 400 }, r.seam));
    svg.appendChild(el("rect", { x: 240, y: y0, width: r.ox["Cr2O3_%"] / 55 * 250, height: y1 - y0, fill: css("--copper"), opacity: isCur ? 1 : .55 }));
    const t = r.pge["4E_ppm"], hi = t.hi == null ? 1000 : t.hi;
    svg.appendChild(el("rect", { x: lx(Math.max(t.lo, .01)), y: y0, width: Math.max(2, lx(hi) - lx(Math.max(t.lo, .01))), height: y1 - y0, fill: css("--teal"), opacity: .25 }));
    svg.appendChild(el("circle", { cx: lx(t.pred), cy: (y0 + y1) / 2, r: isCur ? 5 : 3.5, fill: css("--teal") }));
    svg.appendChild(el("circle", { cx: lx(t.true), cy: (y0 + y1) / 2, r: isCur ? 5 : 3.5, fill: "none", stroke: css("--ink"), "stroke-width": 1.8 }));
    if (isCur) svg.appendChild(el("rect", { x: 4, y: y0 - 2, width: W - 8, height: y1 - y0 + 4, fill: "none", stroke: css("--accent"), "stroke-width": 1.5, rx: 4 })); });
}
$("bvRun").onclick = () => { if (S.bvTimer) { clearInterval(S.bvTimer); S.bvTimer = null; $("bvRun").textContent = "Run parcels"; return; } $("bvRun").textContent = "Pause"; S.bvTimer = setInterval(() => { S.bvIdx++; drawBushveld(); }, +(P.get("parcel") || 2600)); };
$("bvNext").onclick = () => { S.bvIdx++; drawBushveld(); };

/* ---------------- Plant ---------------- */
function plData() { return S.plant[S.plH]; }
function drawPlant() {
  const D = plData(); if (!D) return;
  const ser = D.series, n = ser.length, i = Math.min(S.plIdx, n - 1), svg = $("plChart"); svg.innerHTML = "";
  const W = 900, H = 300, L = 48, R = 12, T = 12, B = 30, vals = ser.flatMap(s => [s.y, s.lo, s.hi, s.persist]).filter(isFinite), lo = Math.min(...vals), hi = Math.max(...vals);
  const x = j => L + j / (n - 1) * (W - L - R), y = v => T + (1 - (v - lo) / (hi - lo)) * (H - T - B), mu = css("--muted"), ln = css("--line");
  for (let v = Math.ceil(lo); v <= hi; v++) { svg.appendChild(el("line", { x1: L, x2: W - R, y1: y(v), y2: y(v), stroke: ln })); svg.appendChild(el("text", { x: L - 6, y: y(v) + 4, "font-size": 10.5, fill: mu, "text-anchor": "end" }, v + "%")); }
  let band = ""; ser.forEach((s, j) => band += (j ? "L" : "M") + x(j) + "," + y(s.hi)); for (let j = n - 1; j >= 0; j--) band += "L" + x(j) + "," + y(ser[j].lo);
  svg.appendChild(el("path", { d: band + "Z", fill: css("--teal"), opacity: .16 }));
  const line = (key, col, w, dash) => { let d = ""; ser.forEach((s, j) => d += (j ? "L" : "M") + x(j).toFixed(1) + "," + y(s[key]).toFixed(1)); svg.appendChild(el("path", { d, fill: "none", stroke: col, "stroke-width": w, "stroke-dasharray": dash || "" })); };
  line("persist", mu, 1.4, "5 4"); line("pred", css("--teal"), 2.2);
  ser.forEach((s, j) => svg.appendChild(el("circle", { cx: x(j), cy: y(s.y), r: 2.2, fill: css("--ink") })));
  svg.appendChild(el("line", { x1: L, x2: W - R, y1: y(D.threshold_upper_illustrative), y2: y(D.threshold_upper_illustrative), stroke: css("--warning-text"), "stroke-dasharray": "6 4" }));
  svg.appendChild(el("line", { x1: x(i), x2: x(i), y1: T, y2: H - B, stroke: css("--accent"), "stroke-width": 1.5 }));
  [0, Math.floor(n / 2), n - 1].forEach(j => svg.appendChild(el("text", { x: x(j), y: H - 8, "font-size": 10.5, fill: mu, "text-anchor": j ? (j === n - 1 ? "end" : "middle") : "start" }, ser[j].issue.slice(5, 16).replace("T", " "))));
  const s = ser[i];
  $("plSub").textContent = `Real plant, test month (September 2017, ${n} hours), forecast issued ${s.issue.replace("T", " ").slice(0, 16)} for ${s.target_time.replace("T", " ").slice(0, 16)} · ${D.horizon_h} h ahead · assumed 2 h lab delay`;
  const G = { "Reagents": ["Starch Flow", "Amina Flow"], "Pulp": ["Ore Pulp Flow", "Ore Pulp pH", "Ore Pulp Density"], "Air flow (mean of 7 columns)": Object.keys(s.tags).filter(k => k.includes("Air Flow")), "Level (mean of 7 columns)": Object.keys(s.tags).filter(k => k.includes("Level")) };
  $("plTags").innerHTML = `<table><tbody>${Object.entries(G).map(([g, ks]) => ks.length > 3 ? `<tr><td>${esc(g)}</td><td class="num">${fmt(ks.map(k => s.tags[k]).filter(v => v != null).reduce((a, b) => a + b, 0) / ks.length)}</td></tr>` : ks.map(k => `<tr><td>${esc(k)}</td><td class="num">${s.tags[k] == null ? "—" : fmt(s.tags[k])}</td></tr>`).join("")).join("")}<tr><td>Latest available lab silica (persistence)</td><td class="num">${fmt(s.persist)} %</td></tr><tr><td>Age of that assay</td><td class="num">${fmt(s.lab_age_h, 0)} h</td></tr></tbody></table>`;
  const code = s.decision === "conservative_default" ? "default" : s.decision;
  const title = { act: "Act: forecast inside the normal band", verify: "Verify: the forecast interval reaches the upper band", default: s.lab_age_h > 5 ? "Conservative default: lab data stale" : "Conservative default: forecast above the band" }[code];
  $("plAdvice").innerHTML = `<div class="hd"><span class="st ${code}">${code === "default" ? "CONSERVATIVE DEFAULT" : code.toUpperCase()}</span><h3>${esc(title)}</h3></div><ul><li>Forecast ${fmt(s.pred)} % silica, 80% interval ${fmt(s.lo)}–${fmt(s.hi)} %; last assay ${fmt(s.persist)} %; band ${fmt(D.threshold_upper_illustrative)} % (training p75, illustrative).</li>${code !== "act" ? "<li>Review amina / starch dosing and column air per site procedure; check the next assay.</li>" : ""}<li>Lab result at ${esc(s.target_time.slice(11, 16))} (revealed later): ${fmt(s.y)} %.</li></ul><div class="note">Decision support only. No setpoint is written.</div>`;
  $("plWhy").innerHTML = `<p><b>What moved this forecast</b> (each tag group replaced by its training mean; association, not cause): ${s.explain.map(e => `${esc(e.group)} ${e.delta >= 0 ? "+" : ""}${fmt(e.delta)} %`).join(" · ")}.</p>`;
  const runs = S.summary.plant.runs, rw = Object.entries(runs).map(([k, r]) => `<tr><td>${esc(k.replace(/^delay(\d+)_h(\d+)$/, "lab delay $1 h · $2 h ahead"))}</td><td class="num">${fmt(r.mae_model)}</td><td class="num">${fmt(r.mae_persistence)}</td><td class="num">${fmt(r.mae_mean)}</td><td>${esc(r.verdict)}</td><td class="num">${Math.round(r.coverage * 100)}%</td></tr>`).join("");
  $("plEvidence").innerHTML = `<table><thead><tr><th>Run</th><th class="num">MAE model</th><th class="num">MAE last assay</th><th class="num">MAE mean</th><th>vs strongest</th><th class="num">80% coverage</th></tr></thead><tbody>${rw}</tbody></table><div class="copy"><p><b>The model does not beat the last lab assay.</b> Once the leakage traps are closed (no same-hour iron assay, an assumed lab delay, hourly bins, a frozen test month), process tags alone cannot forecast concentrate quality better than persistence. Many public results on this dataset report much higher accuracy because they use the same-hour assay.</p><p><b>Why this matters for REEFPRINT:</b> plant tags react after the ore has changed. That is the case for measuring the ore before the plant, on the belt and under the microscope.</p></div>`;
}
$("plH").querySelectorAll("button").forEach(b => b.onclick = () => { S.plH = b.dataset.h; $("plH").querySelectorAll("button").forEach(x => x.classList.toggle("sel", x === b)); drawPlant(); });
$("plRun").onclick = () => { if (S.plTimer) { clearInterval(S.plTimer); S.plTimer = null; $("plRun").textContent = "Replay"; return; } $("plRun").textContent = "Pause"; S.plTimer = setInterval(() => { S.plIdx = (S.plIdx + 1) % plData().series.length; drawPlant(); }, +(P.get("hour") || 700)); };

/* ---------------- Lab round trip ---------------- */
function parseCSV(text) {
  const rows = []; let row = [], f = "", q = false;
  for (let i = 0; i < text.length; i++) { const c = text[i];
    if (q) { if (c === '"' && text[i + 1] === '"') { f += '"'; i++; } else if (c === '"') q = false; else f += c; }
    else if (c === '"') q = true; else if (c === ",") { row.push(f); f = ""; } else if (c === "\n" || c === "\r") { if (c === "\r" && text[i + 1] === "\n") i++; row.push(f); rows.push(row); row = []; f = ""; } else f += c; }
  if (f.length || row.length) { row.push(f); rows.push(row); }
  return rows.filter(r => r.some(x => x.trim() !== ""));
}
function knownSamples() {
  if (S._known) return S._known; const m = new Map();
  for (const rec of ["GEOMET", "MINERAL1"]) for (const [s, h] of Object.entries(S.headers[rec])) m.set(s, { rec, h });
  S.bv.rows.forEach(r => m.set(`${r.bh}@${r.from.toFixed(2)}-${r.to.toFixed(2)}`, { rec: "BUSHVELD", r }));
  return S._known = m;
}
function importCSV(name, text) {
  const REG = new Map(S.reg.targets.map(t => [t.id, t])), rows = parseCSV(text), head = rows.shift() || [], need = ["sample_id", "target_id", "value", "unit", "basis", "size_fraction", "revision", "timestamp"];
  if (rows.length > 20000) return showImport(name, [], [{ line: 0, reason: "File too large for the demo (over 20,000 rows)." }]);
  const miss = need.filter(c => !head.map(h => h.trim()).includes(c));
  if (miss.length) return showImport(name, [], [{ line: 1, reason: "Missing columns: " + miss.join(", ") }]);
  const ix = Object.fromEntries(head.map((h, i) => [h.trim(), i])), ok = [], bad = [], seen = new Set(), known = knownSamples();
  rows.forEach((r, n) => { const g = c => (r[ix[c]] ?? "").trim(), line = n + 2, sid = g("sample_id"), tid = g("target_id"), raw = g("value");
    const rej = reason => bad.push({ line, sample: sid, target: tid, reason });
    if (!/^[A-Za-z0-9_.@\-]{1,64}$/.test(sid)) return rej("Invalid sample id (allowed: letters, digits, _ . @ -).");
    if (/^[=+@\-]/.test(raw) && !/^-?\d/.test(raw)) return rej("Value looks like a spreadsheet formula; refused.");
    const v = Number(raw); if (!isFinite(v)) return rej("Value is not a number.");
    const t = REG.get(tid); if (!t) return rej("Unknown target id (not in registry " + S.reg.version + ").");
    const k = known.get(sid); if (!k) return rej("Unknown sample id.");
    if (k.rec !== t.record) return rej(`Target belongs to ${t.record}, sample belongs to ${k.rec}.`);
    const f = t.units_accepted[g("unit")]; if (f == null) return rej(`Unit "${g("unit")}" not accepted for ${tid} (accepted: ${Object.keys(t.units_accepted).join(", ")}).`);
    if (g("basis") !== t.basis) return rej(`Basis "${g("basis")}" does not match ${t.basis}.`);
    if (t.size_fraction === "none" && g("size_fraction") !== "none") return rej("This target has no size fraction.");
    if (t.size_fraction === "from_sample" && !(k.h.tags || "").split(" ").includes(g("size_fraction"))) return rej("Size fraction does not match the sample.");
    const key = sid + "|" + tid + "|" + g("revision"); if (seen.has(key)) return rej("Duplicate of an earlier row (same sample, target and revision)."); seen.add(key);
    ok.push({ sample: sid, target: tid, value: v * f, rec: k.rec, k }); });
  showImport(name, ok, bad);
}
function showImport(name, ok, bad) {
  S.imported = ok;
  $("importResult").classList.remove("muted");
  $("importResult").innerHTML = `<p><b>${esc(name)}</b>: ${ok.length} rows accepted, ${bad.length} rejected.</p>` + (bad.length ? `<table><thead><tr><th>Line</th><th>Sample</th><th>Target</th><th>Reason</th></tr></thead><tbody>${bad.slice(0, 60).map(b => `<tr><td>${b.line}</td><td>${esc(b.sample || "")}</td><td>${esc(b.target || "")}</td><td>${esc(b.reason)}</td></tr>`).join("")}</tbody></table>` : "");
  audit("import", { detail: `${name}: ${ok.length} accepted, ${bad.length} rejected` });
  reconcile();
}
function predFor(row) {
  if (row.rec === "BUSHVELD") { const k = row.target.split(":")[1], p = row.k.r.pge[k]; return p ? { pred: p.pred, lo: p.lo, hi: p.hi == null ? Infinity : p.hi } : null; }
  const k = row.target.split(":")[1], t = row.k.h.targets[k]; return t ? { pred: t.pred, lo: t.lo, hi: t.hi } : null;
}
function reconcile() {
  const rows = S.imported || []; if (!rows.length) { $("recon").innerHTML = "No accepted rows."; return; }
  const by = {}; rows.forEach(r => { const p = predFor(r); (by[r.target] = by[r.target] || []).push({ r, p }); });
  $("recon").innerHTML = `<table><thead><tr><th>Target</th><th class="num">n</th><th class="num">MAE</th><th class="num">Bias (pred − lab)</th><th class="num">Inside 80% interval</th></tr></thead><tbody>${Object.entries(by).map(([t, xs]) => { const m = xs.filter(x => x.p); if (!m.length) return `<tr><td>${esc(t)}</td><td class="num">${xs.length}</td><td colspan="3">Model input, not a prediction (matched for traceability).</td></tr>`;
    const e = m.map(x => x.p.pred - x.r.value), inside = m.filter(x => x.r.value >= x.p.lo && x.r.value <= x.p.hi).length;
    return `<tr><td>${esc(t)}</td><td class="num">${m.length}</td><td class="num">${fmt(e.reduce((a, b) => a + Math.abs(b), 0) / m.length)}</td><td class="num">${fmt(e.reduce((a, b) => a + b, 0) / m.length)}</td><td class="num">${Math.round(inside / m.length * 100)}%</td></tr>`; }).join("")}</tbody></table><p class="muted">Retrospective reconciliation: these lab values are the public labels the out-of-fold predictions were scored against. A live site would reconcile new assays as they arrive and watch for bias drift.</p>`;
}
$("csvFile").onchange = e => { const f = e.target.files[0]; if (!f) return; if (f.size > 5e6) { showImport(f.name, [], [{ line: 0, reason: "File over 5 MB." }]); return; } f.text().then(t => importCSV(f.name, t)); };
document.querySelectorAll("[data-sample]").forEach(b => b.onclick = () => fetch("live/samples/" + b.dataset.sample).then(r => r.text()).then(t => importCSV(b.dataset.sample, t)));
const neut = s => { s = String(s); return /^[=+\-@]/.test(s) && !/^-?\d+(\.\d+)?$/.test(s) ? "'" + s : s; };
const csvq = s => { s = neut(s); return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; };
function predictionRows() {
  const out = [];
  for (const rec of ["GEOMET", "MINERAL1"]) for (const [s, h] of Object.entries(S.headers[rec])) { const d = decide(rec, h); for (const [k, t] of Object.entries(h.targets)) out.push({ rec, sample: s, k, t, d, used: !!(S.summary.evidence[rec][k] || {}).used_in_decision, ood: h.ood }); }
  return out;
}
function exportKind(kind) {
  const now = new Date().toISOString(), ver = S.summary.hashes_sha256.v6_results.slice(0, 12);
  if (kind === "lims") { const lines = [["sample_id", "record", "target_id", "predicted", "lo_80", "hi_80", "unit", "decision_target", "decision", "ood", "model_sha256_12", "timestamp"].join(",")];
    predictionRows().forEach(p => lines.push([p.sample, p.rec, `${p.rec}:${p.k}`, fmt(p.t.pred, 4), fmt(p.t.lo, 4), fmt(p.t.hi, 4), unit(p.rec, p.k), p.used, p.d.code, p.ood, ver, now].map(csvq).join(",")));
    download("reefprint_lims.csv", lines.join("\n"), "text/csv"); }
  if (kind === "prov") download("reefprint_provenance.json", JSON.stringify({ exported: now, hashes_sha256: S.summary.hashes_sha256, policy: S.summary.policy, registry_version: S.reg.version, evidence: S.summary.evidence, calibration: Object.fromEntries(Object.entries(S.summary.v6_records).map(([k, v]) => [k, v.calibration])), plan: "PLAN-live-v6.md (ClauDex APPROVED, 3 rounds)" }, null, 1), "application/json");
  if (kind === "opcua") { const lines = [["NodeId", "BrowseName", "DataType", "Value", "StatusCode", "SourceTimestamp", "Note"].join(",")];
    predictionRows().filter(p => p.rec === "GEOMET").forEach(p => { const base = `ns=2;s=REEFPRINT.Belt.${p.sample}.${p.k.replace(/\W+/g, "")}`; const q = p.ood === "refused" ? "Bad_OutOfRange" : p.used ? "Good" : "Uncertain_NotUsedForDecision";
      [["Pred", p.t.pred], ["Lo80", p.t.lo], ["Hi80", p.t.hi]].forEach(([n, v]) => lines.push([base + "." + n, n, "Double", fmt(v, 4), q, now, "tag map for a historian or OPC UA server; not a live connection"].map(csvq).join(","))); });
    download("reefprint_opcua_tagmap.csv", lines.join("\n"), "text/csv"); }
  if (kind === "geojson") { const feats = predictionRows().filter(p => p.used || p.rec === "MINERAL1").map(p => ({ type: "Feature", geometry: null, properties: { sample_id: p.sample, record: p.rec, target: p.k, predicted: +fmt(p.t.pred, 4), lo80: +fmt(p.t.lo, 4), hi80: +fmt(p.t.hi, 4), decision: p.d.code, source_location_id: null, note: "No coordinates exist in HIDSAG; join source_location_id from the fleet-management system." } }));
    download("reefprint_parcels.geojson", JSON.stringify({ type: "FeatureCollection", features: feats }, null, 1), "application/geo+json"); }
  if (kind === "report") report();
  audit("export", { detail: kind });
}
document.querySelectorAll("[data-export]").forEach(b => b.onclick = () => exportKind(b.dataset.export));
function report() {
  const rows = Object.entries(S.headers.GEOMET).map(([s, h]) => { const d = decide("GEOMET", h), t = h.targets.WI; return `<tr><td>${esc(s)}</td><td>${fmt(t.pred)} kWh/t (${fmt(t.lo)}–${fmt(t.hi)})</td><td>${esc(h.ood)}</td><td>${esc(d.code)}</td><td>${esc(d.title)}</td></tr>`; }).join("");
  const w = window.open("", "_blank"); if (!w) return;
  w.document.write(`<!doctype html><meta charset="utf-8"><title>REEFPRINT shift report</title><style>body{font-family:Segoe UI,sans-serif;margin:32px;color:#1b2d40}table{border-collapse:collapse;width:100%;font-size:12px}td,th{border-bottom:1px solid #ccd;padding:5px;text-align:left}h1{font-size:22px}.n{color:#536779;font-size:12px}</style><h1>REEFPRINT shift report</h1><p class="n">Generated ${esc(new Date().toISOString())} · model sha256 ${esc(S.summary.hashes_sha256.v6_results.slice(0, 16))} · policy ${esc(S.summary.policy.version)} · replay of public HIDSAG data, not a live belt. Every number on this page is inserted by code from the result files; nothing is written by a language model.</p><h2>Belt: Bond work index (the only target that beat its baseline)</h2><table><tr><th>Sample</th><th>WI (80% interval)</th><th>OOD</th><th>Decision</th><th>Reason</th></tr>${rows}</table><h2>Bushveld</h2><p>Pt, Rh and 4E from chemistry beat the average guess (project-held-out); whether chemistry adds to a known seam is not significant under all gates.</p><h2>Plant</h2><p>The process-tag forecast does not beat the last lab assay once leakage is removed; decision support only.</p><script>print()<\/script>`);
}
function renderRegistry() { $("regVer").textContent = `Version ${S.reg.version} · ${S.reg.targets.length} targets · units, basis and size-fraction rules`; $("registry").innerHTML = `<table><thead><tr><th>Target id</th><th>Type</th><th>Units accepted</th><th>Basis</th></tr></thead><tbody>${S.reg.targets.map(t => `<tr><td>${esc(t.id)}</td><td>${esc(t.analyte_type)}</td><td>${esc(Object.keys(t.units_accepted).join(", "))}</td><td>${esc(t.basis)}</td></tr>`).join("")}</tbody></table>`; }

/* ---------------- Evidence + Where ---------------- */
function renderEvidence() {
  const E = S.summary.evidence, G = E.GEOMET, M = E.MINERAL1, R6 = S.summary.v6_records;
  const v = x => `<span class="badge ${x === "better" ? "ok" : x === "worse" ? "bad" : ""}">${esc(x || "—")}</span>`;
  const gRows = Object.entries(G).map(([k, x]) => `<tr><td>${esc(nice(k))}</td><td class="num">${x.r2_deployable.toFixed(2)}</td><td class="num">${x.r2_full_refit.toFixed(2)}</td><td class="num">${x.r2_v5 != null ? x.r2_v5.toFixed(2) : "—"}</td><td class="num">${x.r2_rgb.toFixed(2)}</td><td>${v(x.vs_baseline)} <span class="muted">vs ${esc(x.strongest_baseline)}</span></td><td>${v(x.vs_v5)}</td><td>${v(x.hs_vs_rgb)}</td><td class="num">${Math.round(x.coverage * 100)}% [${Math.round(x.coverage_ci95[0] * 100)}–${Math.round(x.coverage_ci95[1] * 100)}]</td><td>${x.used_in_decision ? "yes" : "no"}</td></tr>`).join("");
  const mTop = Object.entries(M).sort((a, b) => b[1].r2_full_refit - a[1].r2_full_refit).slice(0, 10).map(([k, x]) => `<tr><td>${esc(nice(k))}</td><td class="num">${x.r2_full_refit.toFixed(2)}</td><td class="num">${x.r2_size_fraction_lookup != null ? x.r2_size_fraction_lookup.toFixed(2) : "—"}</td><td>${v(x.spectrum_adds_over_metadata)}</td><td>${v(x.hs_vs_rgb)}</td><td class="num">${Math.round(x.coverage * 100)}%</td></tr>`).join("");
  const mAdd = Object.values(M).filter(x => x.spectrum_adds_over_metadata === "better").length, mWorse = Object.values(M).filter(x => x.spectrum_adds_over_metadata === "worse").length;
  const ood = r => `${Math.round(R6[r].ood.refused * 100)}% refused, ${Math.round(R6[r].ood.borderline * 100)}% borderline in-domain; shifted-domain acceptance per fold ${R6[r].ood.shift_accept_le_p99_per_fold.map(a => a == null ? "—" : Math.round(a * 100) + "%").join(" / ")}`;
  $("evidence").innerHTML = `
  <div class="panel"><div class="sh"><div><h2>Belt (HIDSAG GEOMET, drill core → lab tests)</h2><p>${R6.GEOMET.n} samples, sample folds (no hole ids exist), deployable model trained on 70% of each outer-training set</p></div></div>
  <table><thead><tr><th>Lab test</th><th class="num">R² deployable</th><th class="num">R² full refit</th><th class="num">R² v5</th><th class="num">R² simulated RGB</th><th>vs strongest baseline</th><th>v6 vs v5</th><th>Hyperspectral vs RGB</th><th class="num">80% coverage</th><th>Drives decisions</th></tr></thead><tbody>${gRows}</tbody></table>
  <div class="copy"><p><b>Reading.</b> Only Bond work index (grinding hardness) clears the strongest baseline under every gate, so it is the only target the belt policy acts on. v6 is not more accurate than v5: v5's numbers were slightly flattered by a k-means leak the ClauDex review found. v6 is the honest version, with calibrated intervals. Hyperspectral is never worse than a simulated colour camera and is better on ${Object.values(G).filter(x => x.hs_vs_rgb === "better").length} of 5 tests.</p><p>OOD gate: ${ood("GEOMET")}.</p></div></div>
  <div class="panel"><div class="sh"><div><h2>Correction: plant-feed mineralogy (HIDSAG MINERAL1, QEMSCAN)</h2><p>${R6.MINERAL1.n} fractions from ${R6.MINERAL1.n_units} composites, grouped folds</p></div><span class="badge bad">changes an earlier claim</span></div>
  <div class="copy"><p>The high R² we showed (chalcopyrite about 0.9) is <b>explained by the size fraction and process line</b>. A lookup of the median for the same line and fraction does as well, and adding the spectrum to that metadata model helped on <b>${mAdd} of ${Object.keys(M).length}</b> minerals and hurt on ${mWorse}. The camera mostly recognised the size fraction. Deck v7 slide 13 ("31 of 33 minerals beat the average guess") is literally true but misleading, and is withdrawn. Rule 3 (report the metadata-only baseline) caught it.</p></div>
  <table><thead><tr><th>Mineral</th><th class="num">R² spectrum model</th><th class="num">R² size-fraction lookup</th><th>Spectrum adds over metadata?</th><th>Hyperspectral vs RGB</th><th class="num">80% coverage</th></tr></thead><tbody>${mTop}</tbody></table><div class="copy muted"><p>OOD gate: ${ood("MINERAL1")}. Blends (sim_): median R² ${R6.MINERAL1.blends ? R6.MINERAL1.blends.median_r2.toFixed(2) : "—"}, beats the mean on ${R6.MINERAL1.blends ? R6.MINERAL1.blends.beats_mean_ci : "—"} of 33 minerals: blended ore is still open.</p></div></div>
  <div class="panel"><div class="sh"><div><h2>Bushveld chromitite: chemistry → PGE (South Africa)</h2><p>${S.summary.bushveld.n_intervals} intervals, ${S.summary.bushveld.n_boreholes} boreholes, ${S.summary.bushveld.n_projects} projects held out by project</p></div></div><div class="copy"><p>Chemistry a belt analyser measures beats the average guess for <b>${Object.entries(S.bv.beats_baseline).filter(([k, v]) => v).map(([k]) => nice(k)).join(", ")}</b> (all gates). It does not for ${Object.entries(S.bv.beats_baseline).filter(([k, v]) => !v).map(([k]) => nice(k)).join(", ")}. If the seam is already known from the mine plan, chemistry's extra gain passes the paired tests but not the doctrine's unpaired gate. Seam from chemistry: ${(S.summary.bushveld.seam.balanced_accuracy * 100).toFixed(0)}% balanced accuracy (majority ${(S.summary.bushveld.seam.balanced_accuracy_majority * 100).toFixed(1)}%). These are lab assays of drill core standing in for a belt reading. A belt pilot is the test.</p></div></div>
  <div class="panel"><div class="sh"><div><h2>Plant: forecasting concentrate silica from process tags</h2><p>Real plant (CC0), time-ordered, frozen test month</p></div></div><div class="copy"><p>At an assumed 2 h lab delay, the 1 h-ahead forecast has MAE ${fmt(S.summary.plant.runs.delay2_h1.mae_model)} % against ${fmt(S.summary.plant.runs.delay2_h1.mae_persistence)} % for the last assay: ${esc(S.summary.plant.runs.delay2_h1.verdict)}. Across every delay and horizon tested it never beats persistence. The 80% intervals cover ${Math.round(S.summary.plant.runs.delay2_h1.coverage * 100)}% in the test month.</p></div></div>
  ${S.summary.pentlandite ? `<div class="panel"><div class="sh"><div><h2>Microscope: the hardest PGM-relevant call (pentlandite vs pyrrhotite)</h2><p>LumenStone S2 (Norilsk), trained on ${S.summary.pentlandite.train_sections} sections, scored on the ${S.summary.pentlandite.val_sections.length} audited validation sections; test sections never opened. Exploratory.</p></div></div><table><thead><tr><th>Given the sulphides are found perfectly…</th><th class="num">Pentlandite IoU</th><th class="num">Precision</th><th class="num">Recall</th></tr></thead><tbody>${Object.entries(S.summary.pentlandite.pooled).map(([k, v]) => `<tr><td>${esc(k)}</td><td class="num">${v.pn_iou.toFixed(2)}</td><td class="num">${isFinite(v.pn_precision) ? v.pn_precision.toFixed(2) : "—"}</td><td class="num">${v.pn_recall.toFixed(2)}</td></tr>`).join("")}</tbody></table><div class="copy"><p>Pentlandite is the main Pd carrier among Bushveld base-metal sulphides, and it looks like pyrrhotite under ordinary reflected light. Even with an oracle sulphide mask, colour and texture separate the two at an IoU of only about 0.5. This is the gap REEFPRINT's rotating-analyser physics targets: pentlandite is isotropic and pyrrhotite anisotropic, an axis that colour does not contain. Identifying pentlandite does not measure Pd content or discrete PGMs.</p></div></div>` : ""}
  <div class="panel"><div class="sh"><div><h2>How the plan was reviewed</h2><p>ClauDex loop: Claude (Opus 5.5) plans, Codex (gpt-6-astra, read-only) attacks</p></div></div><div class="copy"><p>Three rounds, 38 findings, 37 accepted (log: <code>PLAN-live-v6-REVIEW-LOG.md</code>). They changed:</p><ul><li>split-conformal intervals with calibration held out <i>before</i> model selection, and one score per composite;</li><li>strict nesting of k-means, scaling and blends;</li><li>paired gates with Holm correction;</li><li>a total decision table;</li><li>no per-pixel mineral maps (absorption maps instead);</li><li>an assistant that only routes;</li><li>typed lab imports;</li><li>a hardened local proxy.</li></ul></div></div>`;
}
function renderWhere() {
  $("where").innerHTML = `
  <div class="panel"><div class="sh"><div><h2>Model orchestration: one router, one referee, one policy</h2><p>Every input type has its own validated path; nothing is promoted without its evidence bar</p></div></div>
  <table><thead><tr><th>Input</th><th>Router sends it to</th><th>Referee</th><th>What reaches the shift</th></tr></thead><tbody>
  <tr><td>Hyperspectral belt scan (VNIR + SWIR)</td><td>Belt models v6 (per-target nested choice)</td><td>80% split-conformal interval · spectral OOD gate (p95 / p99)</td><td>Bond work index decision; other targets as context</td></tr>
  <tr><td>Belt elemental reading (XRF / PGNAA-type chemistry)</td><td>Chemistry → seam and PGE models (project-held-out)</td><td>80% interval · evidence bar per grade</td><td>PGE routing suggestion (illustrative) or "send for fire assay"</td></tr>
  <tr><td>Polished section (reflected-light micrograph)</td><td>REEFPRINT segmentation (KHANYA workbench) + specialists as candidates</td><td>Quality gate · conformal · refusal</td><td>Liberation, act · verify · hold advice</td></tr>
  <tr><td>Plant time series</td><td>Concentrate-quality soft sensor</td><td>Interval · data freshness</td><td>Decision support (it does not beat the last assay)</td></tr>
  <tr><td>Phone or camera photo</td><td>Quality gates only</td><td>Always outside the validated domain</td><td>"Route to the lab or microscope", with the checks listed</td></tr>
  <tr><td>Lab results (QEMSCAN, XRF, XRD, assays)</td><td>Typed registry import</td><td>Schema, unit, basis and duplicate checks</td><td>Reconciliation; future retraining labels</td></tr></tbody></table></div>
  <div class="panel"><div class="sh"><div><h2>Who decides what, with which signal</h2><p>One question per role. Money levers are where value comes from, not measured gains.</p></div></div><table><thead><tr><th>Role</th><th>Decision</th><th>When</th><th>Signal here</th><th>Money lever</th></tr></thead><tbody>
  <tr><td><b>Control-room operator</b></td><td>Mill feed rate</td><td>minutes</td><td>Belt: Bond work index above its band</td><td>Throughput, kWh per tonne</td></tr>
  <tr><td><b>Shift metallurgist</b></td><td>Reagents, grind target</td><td>hours</td><td>Microscope liberation; plant-view decision support</td><td>Recovery, reagent cost</td></tr>
  <tr><td><b>Concentrator manager / planner</b></td><td>Blend, routing, campaigns</td><td>daily</td><td>Bushveld view: PGE grade and seam from chemistry</td><td>Grade to the PGM circuit, chrome credits</td></tr>
  <tr><td><b>Lab mineralogist</b></td><td>What goes to QEMSCAN / fire assay</td><td>daily</td><td>Refusals, OOD and "verify" queue</td><td>Lab spend where it matters</td></tr>
  <tr><td><b>Data / IT</b></td><td>Integration</td><td>once</td><td>LIMS CSV, OPC UA tag map, GeoJSON, provenance, audit log</td><td>No rework; traceable decisions</td></tr></tbody></table></div>`;
}

/* ---------------- Assistant: route only, templates speak ---------------- */
const TOOLS = ["explain_prediction", "query_samples", "plant_status", "bushveld_status", "compare_with_lab", "switch_view", "export", "generate_report", "help"];
function offlineRoute(q) {
  const s = q.toLowerCase(), id = (q.match(/\b(GMET-\d{4}|M1-\d{4})\b/i) || [])[1];
  if (id && /why|explain|flag|decision|what/.test(s)) return { tool: "explain_prediction", args: { sample_id: id.toUpperCase() } };
  if (/hard|work index|\bwi\b|grind/.test(s)) return { tool: "query_samples", args: { target: "WI", state: "adverse_or_crossing" } };
  if (/verify|flagged|default|refus/.test(s)) return { tool: "query_samples", args: { decision: /default|refus/.test(s) ? "default" : "verify" } };
  if (/plant|silica|amina|starch/.test(s)) return { tool: "plant_status", args: {} };
  if (/bushveld|platinum|pge|\bpt\b|rhodium|chrom|seam/.test(s)) return { tool: "bushveld_status", args: {} };
  if (/reconcil|compare|lab result/.test(s)) return { tool: "compare_with_lab", args: {} };
  if (/report/.test(s)) return { tool: "generate_report", args: {} };
  const ex = s.match(/lims|opc|geojson|qgis|provenance/); if (ex && /export|download|send/.test(s)) return { tool: "export", args: { kind: { lims: "lims", opc: "opcua", geojson: "geojson", qgis: "geojson", provenance: "prov" }[ex[0]] } };
  const v = s.match(/\b(live|scan|bushveld|plant|lab|evidence|where)\b/); if (v && /open|go|show|switch/.test(s)) return { tool: "switch_view", args: { view: v[1] === "scan" ? "live" : v[1] } };
  return { tool: "help", args: {} };
}
function validArgs(r) {
  if (!r || !TOOLS.includes(r.tool)) return { tool: "help", args: {} };
  const a = r.args || {};
  if (r.tool === "explain_prediction" && !(typeof a.sample_id === "string" && /^(GMET|M1)-\d{4}$/.test(a.sample_id))) return { tool: "help", args: { reason: "unknown sample id" } };
  if (r.tool === "switch_view" && !Object.keys(VIEWS).includes(a.view)) return { tool: "help", args: { reason: "unknown view" } };
  if (r.tool === "export" && !["lims", "opcua", "geojson", "prov"].includes(a.kind)) return { tool: "help", args: { reason: "unknown export" } };
  return { tool: r.tool, args: a };
}
function runTool(r) {
  const a = r.args;
  if (r.tool === "explain_prediction") { const rec = a.sample_id.startsWith("GMET") ? "GEOMET" : "MINERAL1", h = S.headers[rec][a.sample_id]; if (!h) return `I don't have ${esc(a.sample_id)} in the showcase set (pre-registered samples only).`;
    const d = decide(rec, h), lines = d.used.map(k => { const t = h.targets[k]; return `${esc(nice(k))} ${fmt(t.pred)} ${esc(unit(rec, k))} (80% interval ${fmt(t.lo)}–${fmt(t.hi)}), state ${esc(d.states[k].s)}; top region: ${esc(t.explain.regions[0].region)}.`; });
    return `<b>${esc(a.sample_id)}</b>: decision <b>${esc(d.code)}</b> (policy row ${d.row}): ${esc(d.title)}.<br>${lines.join("<br>") || esc(d.items[0])}<br><span class="muted">OOD ${esc(h.ood)} · fold ${h.fold + 1}.</span>`; }
  if (r.tool === "query_samples") { const out = [];
    for (const [s, h] of Object.entries(S.headers.GEOMET)) { const d = decide("GEOMET", h); if (a.decision ? d.code === a.decision : (d.states.WI && d.states.WI.s !== "clear")) out.push(`${esc(s)} (WI ${fmt(h.targets.WI.pred)} kWh/t, ${esc(d.code)})`); }
    return out.length ? `${out.length} drill-core showcase samples match: ${out.join(", ")}.` : "No showcase sample matches."; }
  if (r.tool === "plant_status") { const x = S.summary.plant.runs["delay2_h1"]; return `Plant (iron ore, Brazil, CC0): 1 h-ahead forecast MAE ${fmt(x.mae_model)} % silica against ${fmt(x.mae_persistence)} % for the last assay: <b>${esc(x.verdict)}</b> against ${esc(x.strongest_baseline)}; 80% coverage ${Math.round(x.coverage * 100)}%. It is decision support only.`; }
  if (r.tool === "bushveld_status") { const b = S.summary.bushveld, t = b.targets["4E_ppm"]; return `Bushveld chromitite (${b.n_intervals} intervals, ${b.n_projects} projects): 4E R² ${t.r2_chem.toFixed(2)} from chemistry alone, ${t.r2_seam_only.toFixed(2)} from the seam alone, ${t.r2_chem_seam.toFixed(2)} from both; seam balanced accuracy ${(b.seam.balanced_accuracy * 100).toFixed(0)}%.`; }
  if (r.tool === "compare_with_lab") { showView("lab"); return S.imported && S.imported.length ? `Reconciliation is shown in Lab &amp; exports (${S.imported.length} rows).` : "No lab file imported yet. Use Lab &amp; exports to load one."; }
  if (r.tool === "switch_view") { showView(a.view); return `Opened ${esc(VIEWS[a.view][1])}.`; }
  if (r.tool === "export") return `Ready to export <b>${esc(a.kind)}</b>. <button class="btn small" onclick="exportKind('${a.kind}')">Confirm download</button>`;
  if (r.tool === "generate_report") return `The shift report opens a printable page. <button class="btn small" onclick="exportKind('report')">Confirm</button>`;
  return `I can: explain a sample (e.g. "why was GMET-0004 flagged?"), list hard-ore or verify samples, summarise the plant or Bushveld results, reconcile lab files, switch views, or export (LIMS, OPC UA, GeoJSON, provenance).${a.reason ? " (" + esc(a.reason) + ")" : ""}`;
}
async function ask(q) {
  q = q.slice(0, 300); if (!q.trim()) return;
  $("chatlog").insertAdjacentHTML("beforeend", `<div class="msg q"><span>${esc(q)}</span></div>`);
  let r = null, mode = "offline";
  const tok = document.querySelector('meta[name="reef-token"]').content;
  if (tok) { try { const res = await fetch("/api/route", { method: "POST", headers: { "Content-Type": "application/json", "X-Reef-Token": tok }, body: JSON.stringify({ q }) }); const j = await res.json(); if (j.tool) { r = j; mode = j.provider; } } catch (e) {} }
  if (!r) r = offlineRoute(q);
  r = validArgs(r);
  const ans = runTool(r);
  $("chatlog").insertAdjacentHTML("beforeend", `<div class="msg a">${ans}<div class="muted" style="font-size:10.5px;margin-top:4px">tool: ${esc(r.tool)} · router: ${esc(mode)} · answer rendered from code</div></div>`);
  $("chatlog").scrollTop = 1e9; audit("assistant", { detail: `${r.tool} via ${mode}` });
}
$("askBtn").onclick = () => { $("drawer").classList.add("on"); $("askBtn").style.display = "none"; $("askIn").focus(); };
$("askClose").onclick = () => { $("drawer").classList.remove("on"); $("askBtn").style.display = ""; };
$("askGo").onclick = () => { ask($("askIn").value); $("askIn").value = ""; };
$("askIn").addEventListener("keydown", e => { if (e.key === "Enter") $("askGo").click(); });

/* ---------------- Camera: quality gates only ---------------- */
let camStream = null, camImg = null;
$("camBtn").onclick = () => $("camModal").classList.add("on");
$("camClose").onclick = () => { $("camModal").classList.remove("on"); if (camStream) { camStream.getTracks().forEach(t => t.stop()); camStream = null; } };
function camLoad(src) { const cv = $("camCanvas"), sc = Math.min(1, 900 / Math.max(src.width || src.videoWidth, src.height || src.videoHeight)), w = Math.round((src.width || src.videoWidth) * sc), h = Math.round((src.height || src.videoHeight) * sc); cv.width = w; cv.height = h; cv.getContext("2d").drawImage(src, 0, 0, w, h); camImg = cv.getContext("2d").getImageData(0, 0, w, h); camCheck(null); }
$("camFile").onchange = e => { const f = e.target.files[0]; if (!f) return; const img = new Image(); img.onload = () => camLoad(img); img.src = URL.createObjectURL(f); };
$("camLive").onclick = async () => { try { camStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } }); const v = $("camVideo"); v.srcObject = camStream; v.style.display = "block"; $("camSnap").disabled = false; } catch (e) { $("camResult").innerHTML = `<p class="bad">Camera unavailable: ${esc(e.message || e)}</p>`; } };
$("camSnap").onclick = () => camLoad($("camVideo"));
$("camCanvas").addEventListener("click", e => { if (!camImg) return; const cv = $("camCanvas"), r = cv.getBoundingClientRect(); camCheck([Math.floor((e.clientX - r.left) / r.width * cv.width), Math.floor((e.clientY - r.top) / r.height * cv.height)]); });
function camCheck(pt) {
  const { data, width: w, height: h } = camImg, g = new Float32Array(w * h); let clip = 0;
  for (let i = 0; i < w * h; i++) { const r = data[i * 4], gg = data[i * 4 + 1], b = data[i * 4 + 2]; g[i] = .299 * r + .587 * gg + .114 * b; if (Math.max(r, gg, b) >= 250 || Math.min(r, gg, b) <= 5) clip++; }
  let s = 0, s2 = 0, n = 0; for (let y = 1; y < h - 1; y++) for (let x = 1; x < w - 1; x++) { const i = y * w + x, l = 4 * g[i] - g[i - 1] - g[i + 1] - g[i - w] - g[i + w]; s += l; s2 += l * l; n++; }
  const lapVar = s2 / n - (s / n) ** 2, clipF = clip / (w * h);
  const checks = [["Focus (variance of the Laplacian ≥ 60, heuristic)", lapVar >= 60, lapVar.toFixed(0)], ["Exposure (≤ 5% clipped pixels)", clipF <= .05, (clipF * 100).toFixed(1) + "%"]];
  if (pt) { const [cx, cy] = pt, ch = [0, 0, 0], v = []; let m = 0; for (let y = Math.max(0, cy - 10); y < Math.min(h, cy + 10); y++) for (let x = Math.max(0, cx - 10); x < Math.min(w, cx + 10); x++) { const i = (y * w + x) * 4; ch[0] += data[i]; ch[1] += data[i + 1]; ch[2] += data[i + 2]; v.push(g[y * w + x]); m++; }
    const mean = ch.map(c => c / m), mu = v.reduce((a, b) => a + b, 0) / m, sd = Math.sqrt(v.reduce((a, b) => a + (b - mu) ** 2, 0) / m), spread = (Math.max(...mean) - Math.min(...mean)) / Math.max(1, mu);
    checks.push(["Grey or white reference (neutral: channel spread ≤ 12%)", spread <= .12, (spread * 100).toFixed(1) + "%"], ["Reference uniform (std ≤ 12)", sd <= 12, sd.toFixed(1)], ["Reference not clipped (mean 90–235)", mu >= 90 && mu <= 235, mu.toFixed(0)]); }
  else checks.push(["Grey or white reference", false, "click the card in the image"]);
  $("camResult").innerHTML = `<ul class="checks">${checks.map(([n, ok, v]) => `<li class="${ok ? "ok" : "bad"}">${ok ? "✓" : "✗"} ${esc(n)}: ${esc(v)}</li>`).join("")}</ul><div class="advice"><div class="hd"><span class="st default">CONSERVATIVE DEFAULT</span><h3>Outside the validated domain: route the sample to the lab or microscope</h3></div><ul><li>No ore prediction is made from photos: there is no labelled phone-camera dataset to validate against yet.</li><li>What a photo is good for today: a quality check, a record, and a reason to sample.</li></ul></div>`;
  audit("camera_refusal", { detail: checks.map(c => (c[1] ? "pass " : "fail ") + c[0].split(" (")[0]).join("; ") });
}

/* ---------------- boot ---------------- */
function redrawAll() { if (!S.summary) return; if (S.cube) { paint(); drawSpec(); } if ($("v-bushveld").classList.contains("on")) drawBushveld(); if ($("v-plant").classList.contains("on")) drawPlant(); }
window.addEventListener("resize", () => { if (S.cube) paint(); });
async function boot() {
  let t0 = P.get("theme"); if (!t0) { try { t0 = localStorage.getItem("reef-live-theme"); } catch (e) {} } setTheme(["workbench", "mineral-night", "field-paper"].includes(t0) ? t0 : "workbench");
  const get = u => fetch(u).then(r => { if (!r.ok) throw new Error(u + " " + r.status); return r.json(); });
  [S.summary, S.reg, S.bv, S.plant["1"], S.plant["3"]] = await Promise.all(["live/summary.json", "live/targets.json", "live/bushveld.json", "live/plant_h1.json", "live/plant_h3.json"].map(get));
  for (const rec of ["GEOMET", "MINERAL1"]) await Promise.all(S.summary.showcase[rec].map(async s => S.headers[rec][s] = await get(`live/showcase/${rec}/${s}.json`)));
  if (document.querySelector('meta[name="reef-token"]').content) $("askMode").textContent = "Local server connected: a language model routes only if a key is set on the server, otherwise the offline parser · answers always from code";
  renderRegistry(); renderEvidence(); renderWhere(); layerButtons();
  audit("boot", { detail: `loaded ${Object.keys(S.headers.GEOMET).length + Object.keys(S.headers.MINERAL1).length} showcase headers` });
  if (P.get("view") && VIEWS[P.get("view")]) showView(P.get("view"));
  await startScan(S.summary.showcase.GEOMET[0]);
  if (P.get("auto")) $("runBtn").click();
}
boot().catch(e => { document.querySelector("main").insertAdjacentHTML("afterbegin", `<div class="banner" style="background:var(--error-bg);color:var(--error-text)">Could not load the replay data: ${esc(e.message || e)}. Serve this folder with server.py or python -m http.server.</div>`); });
