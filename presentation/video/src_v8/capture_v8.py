"""Record the real REEFPRINT Live app (secure server, guest sandbox) for the v8 demo video.

The recording is paced by the narration (vo/<voice>/durations.json), so the compositor plays it at
real speed. Needs app_server.py on 127.0.0.1:8531. Writes cap/app.webm and cap/marks.json
(seconds from the start of the recording at which each narration line's shot begins).
"""
import asyncio, json, os, shutil, time
from playwright.async_api import async_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
CAP = os.path.join(HERE, "cap")
U = os.environ.get("REEFPRINT_URL", "http://127.0.0.1:8531/")
DUR = json.load(open(os.path.join(HERE, "vo", os.environ.get("REEF_VOICE", "en-GB-RyanNeural"), "durations.json")))
GAP = 0.45


def L(k):
    return int((DUR[k] + GAP) * 1000)


async def main():
    if os.path.isdir(CAP):
        shutil.rmtree(CAP)
    os.makedirs(CAP)
    marks = {}
    async with async_playwright() as p:
        b = await p.chromium.launch(channel="msedge")
        ctx = await b.new_context(viewport={"width": 1920, "height": 1080}, record_video_dir=CAP,
                                  record_video_size={"width": 1920, "height": 1080}, accept_downloads=True)
        t0 = time.monotonic()
        pg = await ctx.new_page()

        def mark(k):
            marks[k] = round(time.monotonic() - t0, 2)
            print(k, marks[k], flush=True)

        async def until(k, ms):  # wait until ms after mark k
            left = marks[k] + ms / 1000 - (time.monotonic() - t0)
            if left > 0:
                await pg.wait_for_timeout(int(left * 1000))

        await pg.goto(U + "?guest=1&scan=900", wait_until="load")
        await pg.wait_for_timeout(2000)
        mark("n08")                                    # belt scan builds; the model predicts
        await until("n08", L("n08"))
        await pg.click("nav.tabs button[data-view='decisions']")
        mark("n09")                                    # the proposal inside the envelope
        await until("n09", L("n09"))
        mark("n10")                                    # countdown, note, approve
        await pg.hover("[data-act='approve']")
        await pg.wait_for_timeout(1200)
        await pg.click("#decNote")
        await pg.keyboard.type("Softer parcel, within envelope", delay=55)
        await pg.wait_for_timeout(1500)
        await pg.click("[data-act='approve']")
        await until("n10", L("n10"))
        mark("n11")                                    # verify the chain, signed checkpoint
        await pg.evaluate("document.querySelector('#ledVerify').scrollIntoView({behavior:'smooth', block:'center'})")
        await pg.wait_for_timeout(1300)
        await pg.click("#ledVerify")
        await pg.wait_for_timeout(2200)
        async with pg.expect_download() as d:
            await pg.click("#ledCheck")
        await (await d.value).path()
        await until("n11", L("n11"))
        await pg.evaluate("window.scrollTo(0,0)")
        await pg.click("nav.tabs button[data-view='evidence']")
        mark("n13")                                    # physics checks, failures included
        await pg.wait_for_timeout(1800)
        for y in range(0, 220, 10):
            await pg.evaluate(f"window.scrollTo(0,{y})")
            await pg.wait_for_timeout(60)
        await until("n13", L("n13"))
        await pg.evaluate("window.scrollTo(0,0)")
        await pg.click("nav.tabs button[data-view='value']")
        mark("n14")                                    # the value chain result
        await pg.wait_for_timeout(1500)
        for y in range(0, 640, 16):
            await pg.evaluate(f"window.scrollTo(0,{y})")
            await pg.wait_for_timeout(45)
        await until("n14", L("n14") + 600)
        mark("end")
        vpath = await pg.video.path()
        await ctx.close()
        await b.close()
    shutil.move(vpath, os.path.join(CAP, "app.webm"))
    json.dump(marks, open(os.path.join(CAP, "marks.json"), "w"), indent=1)


asyncio.run(main())
