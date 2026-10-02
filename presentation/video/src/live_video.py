"""Belt Monitor v2 demo: title card -> real screen recording of the restyled Belt Monitor touring its four views
(scripted clicks timed to the narration) -> end card. Same captions, voice and music engine as the main promo.

python belt_video2.py record   (Belt Monitor served at http://127.0.0.1:8530/)
python belt_video2.py render   -> out/belt2_silent.mp4 + out/timeline_belt2.json
"""
import asyncio, json, os, subprocess, sys, time
import numpy as np

S = os.path.dirname(os.path.abspath(__file__))
sys.argv = [sys.argv[0], "preview"] + sys.argv[1:]
import render as R  # sprites, captions, end card

FF = R.FF
W, H, FPS = R.W, R.H, R.FPS
KEYS = ["l01", "l02", "l03", "l04", "l05", "l06", "l07", "l08", "l09", "l10", "l11"]
REC = os.path.join(S, "out", "live_rec.webm")
TITLE, TAIL = 3.6, 4.0


def timeline():
    t = TITLE + 0.3
    cues = {}
    for k in KEYS:
        cues[k] = t
        t += R.DUR[k] + 0.5
    return cues, t + TAIL


def actions(cues):
    """(time in the final video, javascript), converted to recording time by subtracting TITLE."""
    c = cues
    q = lambda sel: f"document.querySelector({sel!r}).click()"
    return [
        (c["l02"] + 0.0, q("#nextBtn")),
        (c["l03"] + 0.2, q("#sensorSel button[data-s=swir_low]")),
        (c["l03"] + 1.0, q("#layerSel button[data-l=map_swir_aloh]")),
        (c["l04"] + 0.2, q("#modeSel button[data-m='3d']")),
        (c["l05"] + 0.0, q("#modeSel button[data-m='2d']")),
        (c["l06"] + 0.0, q("nav.tabs button[data-view=bushveld]")),
        (c["l06"] + 0.6, q("#bvRun")),
        (c["l07"] + 0.0, q("#bvRun")),
        (c["l07"] + 0.1, q("nav.tabs button[data-view=plant]")),
        (c["l07"] + 0.6, q("#plRun")),
        (c["l08"] + 0.0, q("#plRun")),
        (c["l08"] + 0.1, q("nav.tabs button[data-view=lab]")),
        (c["l08"] + 1.4, q("[data-sample='BAD_mixed_import.csv']")),
        (c["l09"] + 0.0, q("nav.tabs button[data-view=evidence]")),
        (c["l09"] + 2.2, "window.scrollTo({top:620,behavior:'smooth'})"),
        (c["l10"] - 0.2, "window.scrollTo({top:0})"),
        (c["l10"] + 0.0, q("nav.tabs button[data-view=live]")),
        (c["l10"] + 0.4, q("#askBtn")),
        (c["l10"] + 0.9, "document.getElementById('askIn').value='why was GMET-0007 flagged?'"),
        (c["l10"] + 1.6, q("#askGo")),
        (c["l11"] - 0.6, q("#askClose")),
    ]


async def record(seconds, acts):
    from playwright.async_api import async_playwright
    os.makedirs(os.path.join(S, "out", "rec3"), exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(channel="msedge")
        ctx = await b.new_context(viewport={"width": W, "height": H}, record_video_dir=os.path.join(S, "out", "rec3"),
                                  record_video_size={"width": W, "height": H})
        pg = await ctx.new_page()
        t0 = time.monotonic()
        await pg.goto("http://127.0.0.1:8531/?scan=4500&theme=workbench&dwell=60000", wait_until="networkidle")
        for at, js in sorted(acts):
            wait = (at - TITLE) - (time.monotonic() - t0)
            if wait > 0:
                await asyncio.sleep(wait)
            await pg.evaluate(js)
        rest = seconds - (time.monotonic() - t0)
        if rest > 0:
            await asyncio.sleep(rest)
        wall = time.monotonic() - t0
        path = await pg.video.path()
        await ctx.close()
        await b.close()
    os.replace(path, REC)
    json.dump({"wall_s": wall}, open(REC + ".wall.json", "w"))
    print("recorded", REC)


def main():
    mode = sys.argv[2] if len(sys.argv) > 2 else "render"
    cues, total = timeline()
    if mode == "record":
        asyncio.run(record(total - TITLE + 1.5, actions(cues)))
        return
    R.CUE.clear()
    R.CUE.update(cues)
    chunks = R.caption_chunks()
    # Playwright screencasts compress time when frames are dropped; stretch the file back to wall-clock time so the
    # scripted clicks line up with the narration they were timed against.
    import re as _re
    probe = subprocess.run([FF, "-i", REC], capture_output=True, text=True).stderr
    hh, mm, ss = _re.search(r"Duration: (\d+):(\d+):([\d.]+)", probe).groups()
    dur = int(hh) * 3600 + int(mm) * 60 + float(ss)
    wall = json.load(open(REC + ".wall.json"))["wall_s"]
    print("recording", round(dur, 2), "s for", round(wall, 2), "s wall clock; stretch", round(wall / dur, 4))
    dec = subprocess.Popen([FF, "-v", "error", "-i", REC, "-vf", f"setpts={wall / dur:.6f}*PTS,fps={FPS},scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                           stdout=subprocess.PIPE, bufsize=10 ** 7)
    out = os.path.join(S, "out", "live_silent.mp4")
    enc = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    last = np.zeros((H, W, 3), np.uint8)
    pill, pad = R.pill_sprite("REAL APP · REPLAYED PUBLIC DATA", size=17, w=700, fg=R.WHITE, bg=(14, 24, 36, 228), padx=16, pady=9,
                              shadow=12, tracking=1.4, dot=(79, 191, 135))
    end_fn = R.end_card(TAIL, 0)
    for fi in range(int(total * FPS)):
        T = fi / FPS
        if T < TITLE:
            fr = R.navy_bg(T)
            a = R.eout(R.prog(T, 0.2, 0.9))
            e1 = R.text_sprite("REEFPRINT  ·  LIVE", 800, 30, R.ACC, tracking=6)
            R.blit(fr, e1, W / 2 - e1.shape[1] / 2, 380, a)
            t1 = R.text_sprite("Real data. Honest models. Auditable decisions.", 800, 64, R.WHITE)
            R.blit(fr, t1, W / 2 - t1.shape[1] / 2, 440, a)
            t2 = R.text_sprite("Replays of public data in labelled tracks: HIDSAG hyperspectral, Bushveld chromitite assays, a real flotation plant.", 400, 28, (200, 212, 226))
            R.blit(fr, t2, W / 2 - t2.shape[1] / 2, 560, R.eout(R.prog(T, 0.6, 1.3)))
            fr = (fr.astype(np.float32) * (1 - R.prog(T, TITLE - 0.5, TITLE))).astype(np.uint8)
        elif T < total - TAIL + 0.5:
            data = dec.stdout.read(W * H * 3)
            if len(data) == W * H * 3:
                last = np.frombuffer(data, np.uint8).reshape(H, W, 3).copy()
            fr = last.copy()
            if T < TITLE + 0.5:
                fr = (fr.astype(np.float32) * R.prog(T, TITLE, TITLE + 0.5)).astype(np.uint8)
            R.blit(fr, pill, W - 40 - pill.shape[1] + pad, H - 40 - pill.shape[0] + pad, 0.95)
            R.draw_caption(fr, T, chunks, False)
        else:
            fr = end_fn(T - (total - TAIL + 0.5), fi)
            R.draw_caption(fr, T, chunks, True)
        enc.stdin.write(np.ascontiguousarray(fr).tobytes())
    enc.stdin.close()
    enc.wait()
    dec.kill()
    tl = {"total": total, "cues": cues, "clicks": [], "whoosh": [TITLE - 0.2, total - TAIL], "act2": TITLE, "act3": total - TAIL - 6,
          "hit": total - TAIL + 0.5, "captions": chunks}
    json.dump(tl, open(os.path.join(S, "out", "timeline_live.json"), "w"), indent=1)
    print("rendered", out, round(total, 1), "s")


if __name__ == "__main__":
    main()
