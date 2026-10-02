"""Record the real app for the 3-minute cut: desktop (secure server, guest sandbox) paced by narration v8b, with the
on-screen boxes of the elements the narration talks about (for spotlight callouts), and a phone-sized recording of
the public link the QR code opens.

Writes cap_b/app.webm, cap_b/phone.webm, cap_b/marks.json ({"t": {key: s}, "boxes": {key: [[x,y,w,h,label],...]}}).
"""
import asyncio, json, os, shutil, time
from playwright.async_api import async_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
CAP = os.path.join(HERE, "cap_b")
U = os.environ.get("REEFPRINT_URL", "http://127.0.0.1:8531/")
PUBLIC = os.environ.get("REEFPRINT_PUBLIC", "https://lethabomh14-reefprint.static.hf.space/index.html")
DUR = json.load(open(os.path.join(HERE, "vo", "v8b", "durations.json")))
GAP = 0.45


def L(k):
    return int((DUR[k] + GAP) * 1000)


async def desktop(p, marks, boxes):
    b = await p.chromium.launch(channel="msedge")
    ctx = await b.new_context(viewport={"width": 1920, "height": 1080}, record_video_dir=CAP,
                              record_video_size={"width": 1920, "height": 1080}, accept_downloads=True)
    t0 = time.monotonic()
    pg = await ctx.new_page()

    def mark(k):
        marks[k] = round(time.monotonic() - t0, 2)
        print(k, marks[k], flush=True)

    async def until(k, ms):
        left = marks[k] + ms / 1000 - (time.monotonic() - t0)
        if left > 0:
            await pg.wait_for_timeout(int(left * 1000))

    async def box(k, loc, label, panel=False):
        try:
            el = pg.locator(loc).first
            if panel:
                el = el.locator("xpath=ancestor::div[contains(concat(' ', normalize-space(@class), ' '), ' panel ')][1]")
            bb = await el.bounding_box()
            if bb:
                boxes.setdefault(k, []).append([round(bb["x"]), round(bb["y"]), round(bb["width"]), round(bb["height"]), label])
        except Exception as e:
            print("box failed", k, loc, e)

    await pg.goto(U + "?guest=1&scan=700", wait_until="load")
    await pg.wait_for_timeout(2500)
    await pg.click("#viewOpt button[data-o='smooth']")
    mark("n09")
    await until("n09", L("n09"))
    mark("n10")
    await pg.click("#runBtn")
    await pg.wait_for_timeout(800)
    await box("n10", "#belt", "1 · SCAN: the belt, line by line")
    await until("n10", L("n10"))
    mark("n11")
    await pg.click("#sensorSel button[data-s='swir_low']")
    await pg.wait_for_timeout(500)
    await pg.click("#layerSel button[data-l='map_swir_aloh']")
    await box("n11", "#layerSel", "2 · SEE: absorption maps")
    await pg.wait_for_timeout(int(L("n11") * 0.3))
    await pg.click("#layerSel button[data-l='clusters']")
    await pg.wait_for_timeout(int(L("n11") * 0.3))
    await pg.click("#modeSel button[data-m='3d']")
    await until("n11", L("n11"))
    await pg.click("#modeSel button[data-m='belt']")
    await pg.click("#sensorSel button[data-s='vnir_low']")
    mark("n12")
    await box("n12", "text=Before grinding", "3 · PREDICT: hardness with an honest bound", panel=True)
    await until("n12", L("n12"))
    await pg.click("#runBtn")                                   # pause the belt so the decision stays on one parcel
    await pg.click("nav.tabs button[data-view='decisions']")
    mark("n13")
    await pg.wait_for_timeout(700)
    await box("n13", "#decState", "4 · DECIDE: a proposal inside the envelope", panel=True)
    await box("n13", "text=Operating envelope", "site-approved limits", panel=True)
    await until("n13", L("n13"))
    mark("n14")
    await box("n14", "#decState", "90-second countdown")
    await pg.hover("[data-act='approve']")
    await pg.wait_for_timeout(900)
    await pg.click("#decNote")
    await pg.keyboard.type("Softer parcel, within envelope", delay=55)
    await pg.wait_for_timeout(900)
    await box("n14", "[data-act='approve']", "a person approves")
    await pg.click("[data-act='approve']")
    await until("n14", L("n14"))
    mark("n15")
    await pg.evaluate("document.querySelector('#ledVerify').scrollIntoView({block:'center'})")
    await pg.wait_for_timeout(700)
    await pg.click("#ledVerify")
    await pg.wait_for_timeout(1500)
    async with pg.expect_download() as d:
        await pg.click("#ledCheck")
    await (await d.value).path()
    await pg.wait_for_timeout(600)
    await box("n15", "#ledState", "5 · RECORD: chain intact, post-quantum signed", panel=True)
    await until("n15", L("n15"))
    await pg.evaluate("window.scrollTo(0,0)")
    mark("n16")
    await pg.click("#askBtn")
    await pg.wait_for_timeout(600)
    await pg.click("#askIn")
    await pg.keyboard.type("why was GMET-0048 refused?", delay=45)
    await pg.keyboard.press("Enter")
    await pg.wait_for_timeout(900)
    await box("n16", "#drawer", "Ask REEFPRINT: answers from the data")
    await until("n16", L("n16"))
    await pg.click("#askClose")
    await pg.click("nav.tabs button[data-view='evidence']")
    mark("n18")
    await pg.wait_for_timeout(600)
    await box("n18", "text=Is it physically possible?", "every claim against its physics", panel=True)
    await until("n18", L("n18"))
    await pg.click("nav.tabs button[data-view='value']")
    mark("n19")
    await pg.wait_for_timeout(700)
    for y in range(0, 560, 20):
        await pg.evaluate(f"window.scrollTo(0,{y})")
        await pg.wait_for_timeout(35)
    await pg.wait_for_timeout(400)
    await box("n19", "text=throughput vs no ore information", "+1.9% tonnes (simulated)", panel=True)
    await until("n19", L("n19") + 500)
    mark("end")
    vpath = await pg.video.path()
    await ctx.close()
    await b.close()
    shutil.move(vpath, os.path.join(CAP, "app.webm"))


async def phone(p):
    b = await p.chromium.launch(channel="msedge")
    ctx = await b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True,
                              record_video_dir=CAP, record_video_size={"width": 780, "height": 1688})
    pg = await ctx.new_page()
    await pg.goto(PUBLIC + "?guest=1&scan=700", wait_until="load")
    await pg.wait_for_timeout(3500)
    for y in range(0, 900, 25):
        await pg.evaluate(f"window.scrollTo(0,{y})")
        await pg.wait_for_timeout(60)
    await pg.wait_for_timeout(1200)
    await pg.evaluate("window.scrollTo(0,0)")
    await pg.evaluate("document.querySelector(\"nav.tabs button[data-view='decisions']\").click()")
    await pg.wait_for_timeout(2500)
    await pg.evaluate("document.querySelector(\"[data-act='approve']\").scrollIntoView({block:'center'})")
    await pg.wait_for_timeout(800)
    await pg.tap("[data-act='approve']")
    await pg.wait_for_timeout(3000)
    vpath = await pg.video.path()
    await ctx.close()
    await b.close()
    shutil.move(vpath, os.path.join(CAP, "phone.webm"))


async def main():
    if os.path.isdir(CAP):
        shutil.rmtree(CAP)
    os.makedirs(CAP)
    marks, boxes = {}, {}
    async with async_playwright() as p:
        await desktop(p, marks, boxes)
        await phone(p)
    json.dump({"t": marks, "boxes": boxes}, open(os.path.join(CAP, "marks.json"), "w"), indent=1)
    print("boxes:", {k: len(v) for k, v in boxes.items()})


asyncio.run(main())
