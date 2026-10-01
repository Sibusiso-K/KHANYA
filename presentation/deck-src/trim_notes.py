"""Bring the v7 talk back toward 10 minutes: delete redundant sentences only (no new claims), tighten the three new notes,
and update SCRIPT_13 with the finished FCN ensemble validation (training/ensemble-validation-20261001/fcn-seed42)."""
import io, json, os, re

D = os.path.dirname(os.path.abspath(__file__))
sp = os.path.join(D, "script_notes.json")
N = json.load(io.open(sp, encoding="utf-8"))
tag = re.compile(r"^\[[^\]]*\]\s*")
for k in N:
    if not N[k].startswith("[APPENDIX"):
        N[k] = tag.sub("", N[k])

cuts = {
    "SCRIPT_2": [" At a major commercial lab, one week is the expedited turnaround."],
    "SCRIPT_2b": [" It's the reference, but it's lab-bound, slow and costly."],
    "SCRIPT_2c": [("A mineralogist can name the minerals, but they're scarce, usually in a central lab, and putting numbers on proportions and liberation takes hours of point counting.",
                   "A mineralogist can name the minerals, but they're scarce, and quantifying liberation takes hours.")],
    "SCRIPT_5": [" Around those three you also get grain liberation, XRF context, a spatial view and a phone view."],
    "SCRIPT_6": [" You use standard sample preparation and any lab microscope camera."],
    "SCRIPT_8": [" A fresh analysis took ninety-eight seconds on a laptop CPU."],
    "SCRIPT_9": [" XRD is bulk and slow.",
                 ("Core-scale hyperspectral struggles with opaque minerals.", "Hyperspectral reads gangue, not opaque minerals, which is why we pair it with the microscope."),
                 (" It complements all of them, and referring only uncertain samples to QEMSCAN is a workflow we'll validate in the pilot.", " It complements all of them.")],
    "SCRIPT_10": [("First, triage.", "Triage, first."), " Second, decisions happen inside the shift. Third, it never acts on thin evidence."],
    "SCRIPT_11": [" works on a phone,"],
}
for k, ops in cuts.items():
    for op in ops:
        a, b = (op, "") if isinstance(op, str) else op
        assert N[k].count(a) == 1, (k, a)
        N[k] = N[k].replace(a, b)

N["SCRIPT_6b"] = ("Where does it sit? Three instruments, three speeds. On the mill-feed belt, a hyperspectral camera reads the host rock in "
                  "seconds and flags an ore change. In the shift lab, REEFPRINT reads the payable sulphides and their liberation. QEMSCAN, "
                  "days later, teaches both. One control-room screen, and only a setpoint a person approves reaches the plant.")
N["SCRIPT_8b"] = ("We tested the belt idea today on public hyperspectral scans of a hundred and forty-six drill-core samples. From the "
                  "spectrum alone, all five lab results beat the average guess, modestly: R squared zero point two seven to zero point "
                  "three seven. An early warning, not a replacement for the lab.")
N["SCRIPT_8c"] = ("And this is the new part: QEMSCAN as the teacher. Trained on its labels, the camera estimated plant-feed mineralogy "
                  "for composites it had never seen. Thirty-one of thirty-three minerals beat the average guess; chalcopyrite reached "
                  "zero point eight nine. Honestly, it reads the alteration minerals that travel with copper here, so every mine "
                  "calibrates on its own QEMSCAN. On Bushveld ore it would track talc and silicate gangue; that is untested.")
N["SCRIPT_13"] = ("Different models are good at different minerals. The live model misses magnetite, the candidate finds it, and the "
                  "historical model is best on pyrrhotite and pentlandite. So next, a router sends each image to specialists, weighted "
                  "on validation data, with a conformal referee deciding answer, verify or hold. The first new member finished today: "
                  "averaged in, it lowered validation mean IoU from zero point seven zero to zero point six nine, so it stays out.")

order = ["SCRIPT_1", "SCRIPT_2", "SCRIPT_2b", "SCRIPT_2c", "SCRIPT_3", "SCRIPT_4", "SCRIPT_5", "SCRIPT_6", "SCRIPT_6b", "SCRIPT_7",
         "SCRIPT_8", "SCRIPT_8b", "SCRIPT_8c", "SCRIPT_9", "SCRIPT_10", "SCRIPT_10b", "SCRIPT_11", "SCRIPT_12", "SCRIPT_13",
         "SCRIPT_14", "SCRIPT_15", "SCRIPT_16"]
WPS, VIDEO, GAP = 2.75, 90.0, 1.0
t = 0.0


def mmss(x):
    x = int(round(x))
    return f"{x // 60}:{x % 60:02d}"


for k in order:
    dur = len(N[k].split()) / WPS + (VIDEO if k == "SCRIPT_7" else 0) + GAP
    N[k] = f"[{mmss(t)}–{mmss(t + dur)}] " + N[k]
    t += dur
print("total", mmss(t), "at", round(WPS * 60), "wpm")
json.dump(N, io.open(sp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
