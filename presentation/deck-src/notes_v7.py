"""v7 speaker notes: add 6b/8b/8c, move 13b to the appendix, retime every slide from its word count.
Pace 2.75 words/s (165 wpm, brisk but clear); slide 7 adds the 90 s promo. Timings are computed, not typed."""
import io, json, os, re

D = os.path.dirname(os.path.abspath(__file__))
# 1) move the reference-spectra slide (13b) to the appendix, ahead of the sources
p = os.path.join(D, "build_deck.py")
s = io.open(p, encoding="utf-8").read()
a = s.index("# ---- 13b SPECTRAL")
b = s.index("# ---- 14 ROADMAP")
block = s[a:b]
if s.index("# ---- APPENDIX A") > b:
    s = s[:a] + s[b:]
    s = s.replace("# ---- APPENDIX A", block.replace("# ---- 13b SPECTRAL", "# ---- APPENDIX 0 (was 13b) SPECTRAL") + "# ---- APPENDIX A", 1)
s = s.replace("opaque (slide on reference spectra)", "opaque (appendix: reference spectra)")
io.open(p, "w", encoding="utf-8").write(s)

# 2) notes
sp = os.path.join(D, "script_notes.json")
N = json.load(io.open(sp, encoding="utf-8"))
N["SCRIPT_6b"] = ("Where does it sit? Three instruments, three speeds. On the mill-feed belt, a hyperspectral camera reads the host rock "
                  "in seconds and flags an ore change. In the shift lab, REEFPRINT reads the payable sulphides and how they are locked, "
                  "within the shift. QEMSCAN, days later, teaches both. One screen in the control room, and only a setpoint a person "
                  "approves reaches the plant.")
N["SCRIPT_8b"] = ("We tested the belt idea today, on public hyperspectral scans of a hundred and forty-six drill-core samples with lab "
                  "flotation and grinding tests. From the spectrum alone, all five lab results beat the average guess, but modestly: "
                  "R squared from zero point two seven to zero point three seven. That is an early warning, not a replacement for the lab. "
                  "On the right, the Belt Monitor replays held-out samples, one by one.")
N["SCRIPT_8c"] = ("And this is the new part. QEMSCAN is slow but exact, so we made it the teacher. Trained on QEMSCAN labels, the camera "
                  "estimated plant-feed mineralogy for composites it had never seen: thirty-one of thirty-three minerals beat the average "
                  "guess, and chalcopyrite, the copper mineral, reached an R squared of zero point eight nine. To be straight with you: it "
                  "reads the alteration minerals that travel with copper in this deposit, so every mine calibrates on its own QEMSCAN. On "
                  "Bushveld ore it would track talc and silicate gangue. That is still untested.")
order = ["SCRIPT_1", "SCRIPT_2", "SCRIPT_2b", "SCRIPT_2c", "SCRIPT_3", "SCRIPT_4", "SCRIPT_5", "SCRIPT_6", "SCRIPT_6b", "SCRIPT_7",
         "SCRIPT_8", "SCRIPT_8b", "SCRIPT_8c", "SCRIPT_9", "SCRIPT_10", "SCRIPT_10b", "SCRIPT_11", "SCRIPT_12", "SCRIPT_13",
         "SCRIPT_14", "SCRIPT_15", "SCRIPT_16"]
WPS, VIDEO = 2.75, 90.0
t = 0.0
tag = re.compile(r"^\[\d+:\d\d.\d+:\d\d\]\s*")


def mmss(x):
    x = int(round(x))
    return f"{x // 60}:{x % 60:02d}"


for k in order:
    body = tag.sub("", N[k])
    dur = len(body.split()) / WPS + (VIDEO if k == "SCRIPT_7" else 0) + 1.5
    N[k] = f"[{mmss(t)}–{mmss(t + dur)}] " + body
    print(f"{k:11s} {mmss(t)}–{mmss(t + dur)}")
    t += dur
N["SCRIPT_13b"] = "[APPENDIX — Q&A backup] " + tag.sub("", N["SCRIPT_13b"])
print("total", mmss(t))
json.dump(N, io.open(sp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
