"""Resumable, one-process-at-a-time renderer: survives out-of-memory crashes by continuing from the
last frame actually written, then concatenates the parts and muxes the soundtrack.

python drive.py full|cut90
"""
import json, os, re, subprocess, sys, time

S = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(S, "out")
FF = r"C:\Users\USER\Desktop\REEFPRINT\.workbench\media-tools\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe"
DEST = r"C:\Users\USER\Desktop\REEFPRINT\presentation\video"
which = sys.argv[1]
cut = which == "cut90"
tl = json.load(open(os.path.join(OUT, "timeline90.json" if cut else "timeline.json")))
total_frames = int(-(-tl["total"] * 30 // 1))
tag = "c90" if cut else "full"


def frames(path):
    if not os.path.exists(path) or os.path.getsize(path) < 1000:
        return 0
    r = subprocess.run([FF, "-v", "error", "-i", path, "-map", "0:v:0", "-c", "copy", "-f", "null", "-", "-stats"],
                       capture_output=True, text=True)
    m = re.findall(r"frame=\s*(\d+)", r.stderr)
    return int(m[-1]) if m else 0


parts = []
f = 0
k = 0
while f < total_frames and k < 25:
    name = f"d_{tag}_{k:02d}.mp4"
    path = os.path.join(OUT, name)
    if os.path.exists(path):
        os.remove(path)
    cmd = [sys.executable, os.path.join(S, "render.py"), "full", "--from", f"{f / 30:.6f}", "--to", "9999", "--out", name]
    if cut:
        cmd.append("--cut90")
    log = open(os.path.join(S, f"drive_{tag}.log"), "a")
    log.write(f"\n--- part {k} from frame {f} at {time.strftime('%H:%M:%S')}\n")
    log.flush()
    subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, cwd=S)
    time.sleep(2)
    n = frames(path)
    log.write(f"part {k}: wrote {n} frames\n")
    log.close()
    if n > 0:
        parts.append(name)
        f += n
    k += 1
print(tag, "rendered", f, "of", total_frames, "frames in", len(parts), "parts", flush=True)
if f < total_frames:
    sys.exit(f"incomplete: {f}/{total_frames}")
lst = os.path.join(OUT, f"d_{tag}_concat.txt")
open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
silent = os.path.join(OUT, f"d_{tag}_silent.mp4")
subprocess.run([FF, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent], check=True)
assert frames(silent) == total_frames, "frame count mismatch after concat"
audio = os.path.join(OUT, "audio90.wav" if cut else "audio.wav")
final = os.path.join(DEST, "REEFPRINT-promo-90s.mp4" if cut else "REEFPRINT-promo-full.mp4")
tmp = final + ".tmp.mp4"
subprocess.run([FF, "-v", "error", "-y", "-i", silent, "-i", audio, "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
                "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", tmp], check=True)
os.replace(tmp, final)
print("wrote", final, os.path.getsize(final), flush=True)
