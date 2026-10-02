"""Belt Monitor demo clip: title card -> real screen recording of the running Belt Monitor -> end card,
with en-GB narration, captions and the same original music engine as the main promo.

python belt_video.py record   (needs the page served at http://127.0.0.1:8530/)
python belt_video.py render
"""
import json, os, subprocess, sys, asyncio
import numpy as np

S = os.path.dirname(os.path.abspath(__file__))
sys.argv = [sys.argv[0], "preview"] + sys.argv[1:]
import render as R  # reuse sprites, captions, finishing

FF = R.FF
W, H, FPS = R.W, R.H, R.FPS
KEYS = ["h01", "h02", "h03", "h04", "h05", "h06"]
REC = os.path.join(S, "out", "belt_rec.webm")
TITLE, TAIL = 3.6, 4.0


def timeline():
    t = TITLE + 0.3
    cues = {}
    for k in KEYS:
        cues[k] = t
        t += R.DUR[k] + 0.45
    total = t + TAIL
    return cues, total


async def record(seconds):
    from playwright.async_api import async_playwright
    os.makedirs(os.path.join(S, "out", "rec"), exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(channel="msedge")
        ctx = await b.new_context(viewport={"width": W, "height": H}, record_video_dir=os.path.join(S, "out", "rec"),
                                  record_video_size={"width": W, "height": H})
        pg = await ctx.new_page()
        await pg.goto("http://127.0.0.1:8530/?speed=4300", wait_until="networkidle")
        await pg.wait_for_timeout(int(seconds * 1000))
        path = await pg.video.path()
        await ctx.close()
        await b.close()
    os.replace(path, REC)
    print("recorded", REC)


def main():
    mode = sys.argv[2] if len(sys.argv) > 2 else "render"
    cues, total = timeline()
    if mode == "record":
        asyncio.run(record(total - TITLE + 1.5))
        return
    R.CUE.clear()
    R.CUE.update(cues)
    chunks = R.caption_chunks()
    rec_len = total - TITLE
    dec = subprocess.Popen([FF, "-v", "error", "-i", REC, "-t", f"{rec_len + 0.5:.2f}", "-vf", f"fps={FPS},scale={W}:{H}",
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE, bufsize=10 ** 7)
    out = os.path.join(S, "out", "belt_silent.mp4")
    enc = subprocess.Popen([FF, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    last = np.zeros((H, W, 3), np.uint8)
    n = int(total * FPS)
    for fi in range(n):
        T = fi / FPS
        if T < TITLE:
            fr = R.navy_bg(T)
            a = R.eout(R.prog(T, 0.2, 0.9))
            e1 = R.text_sprite("REEFPRINT  ·  BELT MONITOR", 800, 30, R.ACC, tracking=6)
            R.blit(fr, e1, W / 2 - e1.shape[1] / 2, 380, a)
            t1 = R.text_sprite("Hyperspectral, before grinding.", 800, 72, R.WHITE)
            R.blit(fr, t1, W / 2 - t1.shape[1] / 2, 440, a)
            t2 = R.text_sprite("Replay of public HIDSAG samples (CC0) — real model, real spectra, not a live belt.", 400, 28, (200, 212, 226))
            R.blit(fr, t2, W / 2 - t2.shape[1] / 2, 560, R.eout(R.prog(T, 0.6, 1.3)))
            fo = 1 - R.prog(T, TITLE - 0.5, TITLE)
            fr = (fr.astype(np.float32) * fo + last.astype(np.float32) * 0).astype(np.uint8)
        elif T < total - TAIL + 0.5:
            data = dec.stdout.read(W * H * 3)
            if len(data) == W * H * 3:
                last = np.frombuffer(data, np.uint8).reshape(H, W, 3).copy()
            fr = last.copy()
            if T < TITLE + 0.5:
                fr = (fr.astype(np.float32) * R.prog(T, TITLE, TITLE + 0.5)).astype(np.uint8)
            spr, pad = R.pill_sprite("REAL APP · REPLAYED PUBLIC DATA", size=17, w=700, fg=R.WHITE, bg=(14, 24, 36, 228), padx=16, pady=9, shadow=12, tracking=1.4, dot=(79, 191, 135))
            R.blit(fr, spr, W - 40 - spr.shape[1] + pad, H - 40 - spr.shape[0] + pad, 0.95)
            R.draw_caption(fr, T, chunks, False)
        else:
            fr = R.end_card(TAIL, 0)(T - (total - TAIL + 0.5), fi)
            R.draw_caption(fr, T, chunks, True)
        enc.stdin.write(np.ascontiguousarray(fr).tobytes())
    enc.stdin.close()
    enc.wait()
    dec.kill()
    tl = {"total": total, "cues": cues, "clicks": [], "whoosh": [TITLE - 0.2, total - TAIL], "act2": TITLE, "act3": total - TAIL - 6,
          "hit": total - TAIL + 0.5, "captions": chunks}
    json.dump(tl, open(os.path.join(S, "out", "timeline_belt.json"), "w"), indent=1)
    print("rendered", out, round(total, 1), "s")


if __name__ == "__main__":
    main()
