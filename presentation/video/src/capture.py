import asyncio, sys, time, os
from playwright.async_api import async_playwright

OUT = sys.argv[1]
os.makedirs(OUT + "/run", exist_ok=True)
URL = "http://127.0.0.1:8510/"
log = open(f"{OUT}/capture_log.txt", "w", encoding="utf-8")


def L(*a):
    s = " ".join(map(str, a))
    print(s, flush=True)
    log.write(s + "\n")
    log.flush()


async def shot(pg, name, full=False):
    await pg.screenshot(path=f"{OUT}/{name}.png", full_page=full)
    L("shot", name)


async def nav(pg, name):
    await pg.get_by_role("button", name=name, exact=True).first.click()
    await pg.wait_for_timeout(1800)
    await pg.evaluate("window.scrollTo(0,0)")
    await pg.wait_for_timeout(400)


async def step(title, coro):
    try:
        await coro
    except Exception as e:
        L("FAILED", title, repr(e)[:400])


BUSY_JS = """() => {
  const b = [...document.querySelectorAll('button')].find(x => /Run analysis|Analys|Cancel|Stop|Running/i.test(x.textContent));
  return b ? (b.textContent.trim() + '|' + b.disabled) : 'none';
}"""


async def desktop(b, run_live):
    ctx = await b.new_context(viewport={"width": 1920, "height": 1080})
    pg = await ctx.new_page()
    await pg.goto(URL, wait_until="networkidle")
    await pg.wait_for_timeout(2500)
    await shot(pg, "d01_dashboard")

    async def ws():
        await nav(pg, "Workspace")
        await shot(pg, "d02_ws_before")
        if run_live:
            await pg.get_by_role("button", name="Run analysis").first.click()
            t0 = time.time()
            i = 0
            idle = 0
            while time.time() - t0 < 220:
                await pg.screenshot(path=f"{OUT}/run/f{i:04d}.png")
                busy = await pg.evaluate(BUSY_JS)
                if i % 10 == 0:
                    L(f"run t={time.time() - t0:.1f} btn={busy}")
                if busy.startswith("Run analysis|false") and time.time() - t0 > 8:
                    idle += 1
                    if idle >= 4:
                        break
                i += 1
                await pg.wait_for_timeout(450)
            L("run frames", i, "elapsed", round(time.time() - t0, 1))
            await pg.wait_for_timeout(1500)
        await shot(pg, "d03_ws_after")
        await shot(pg, "d03_ws_after_full", True)
        open(f"{OUT}/d03_ws_after.txt", "w", encoding="utf-8").write(await pg.inner_text("main"))
        for v in ["Original", "Phase mask", "Compare", "Phase overlay"]:
            await pg.get_by_role("button", name=v, exact=True).first.click()
            await pg.wait_for_timeout(1300)
            await shot(pg, "d04_view_" + v.replace(" ", "_"))
        n = await pg.locator("input[type=range]").count()
        for k in range(n):
            lab = await pg.locator("input[type=range]").nth(k).get_attribute("aria-label")
            L("range", k, lab)
        g = pg.get_by_role("button", name="Grain 4", exact=True).first
        await g.scroll_into_view_if_needed()
        await g.click()
        await pg.wait_for_timeout(1800)
        hdr = pg.get_by_text("Explore individual grains").first
        await hdr.scroll_into_view_if_needed()
        await pg.evaluate("window.scrollBy(0,-90)")
        await pg.wait_for_timeout(800)
        await shot(pg, "d05_grain4_top")
        await pg.evaluate("window.scrollBy(0,700)")
        await pg.wait_for_timeout(600)
        await shot(pg, "d05_grain4_mid")
        g = pg.get_by_role("button", name="Grain 14", exact=True).first
        await g.click()
        await pg.wait_for_timeout(1500)
        await hdr.scroll_into_view_if_needed()
        await pg.evaluate("window.scrollBy(0,-90)")
        await pg.wait_for_timeout(800)
        await shot(pg, "d05_grain14_top")
        await shot(pg, "d05_ws_full_grain", True)
        x = pg.get_by_text("Elemental context").first
        await x.scroll_into_view_if_needed()
        await pg.evaluate("window.scrollBy(0,-300)")
        await pg.wait_for_timeout(700)
        await shot(pg, "d06_xrf_validation")
        x = pg.get_by_text("From prediction to process decision").first
        await x.scroll_into_view_if_needed()
        await pg.evaluate("window.scrollBy(0,-120)")
        await pg.wait_for_timeout(700)
        await shot(pg, "d07_ws_decision")

    await step("workspace", ws())

    async def rep():
        await nav(pg, "Reports")
        await shot(pg, "d08_reports")
        await shot(pg, "d08_reports_full", True)
        open(f"{OUT}/d08_reports.txt", "w", encoding="utf-8").write(await pg.inner_text("main"))
        await pg.get_by_role("link", name="Retrained candidate").first.click()
        await pg.wait_for_timeout(1800)
        await shot(pg, "d09_candidate")
        await pg.evaluate("window.scrollBy(0,800)")
        await pg.wait_for_timeout(700)
        await shot(pg, "d09_candidate2")

    await step("reports", rep())

    async def proc():
        await nav(pg, "Process")
        await shot(pg, "d10_process")
        await pg.get_by_role("button", name="Test in simulator").first.click()
        await pg.wait_for_timeout(6000)
        await shot(pg, "d11_process_sim")
        await shot(pg, "d11_process_sim_full", True)
        open(f"{OUT}/d11_process.txt", "w", encoding="utf-8").write(await pg.inner_text("main"))
        x = pg.get_by_text("Export the decision evidence").first
        await x.scroll_into_view_if_needed()
        await pg.wait_for_timeout(600)
        await shot(pg, "d12_process_export")

    await step("process", proc())

    async def spat():
        await nav(pg, "Spatial")
        await shot(pg, "d13_spatial_empty")
        await pg.get_by_label("Show synthetic demo scene (not real data)").check()
        await pg.wait_for_timeout(3500)
        await shot(pg, "d14_spatial_3d")
        x = pg.get_by_text("Scene layers").first
        await x.scroll_into_view_if_needed()
        await pg.evaluate("window.scrollBy(0,-160)")
        await pg.wait_for_timeout(1200)
        await shot(pg, "d14_spatial_3d_scrolled")
        for nm in ["Plan map", "E-W section", "3D model"]:
            await pg.get_by_role("button", name=nm).first.click()
            await pg.wait_for_timeout(2200)
            await shot(pg, "d15_spatial_" + nm.replace(" ", "_").replace("-", ""))
        open(f"{OUT}/d14_spatial.txt", "w", encoding="utf-8").write(await pg.inner_text("main"))
        await pg.get_by_label("Show synthetic demo scene (not real data)").uncheck()
        await pg.wait_for_timeout(800)

    await step("spatial", spat())

    async def samp():
        await nav(pg, "Samples")
        await shot(pg, "d16_samples")

    await step("samples", samp())

    async def asst():
        await nav(pg, "Workspace")
        await pg.get_by_role("button", name="Ask the evidence").first.click()
        await pg.wait_for_timeout(2000)
        await shot(pg, "d17_assistant_open")
        open(f"{OUT}/d17_assistant.txt", "w", encoding="utf-8").write(await pg.inner_text("body"))
        btns = await pg.evaluate(
            "() => [...document.querySelectorAll('aside button, [role=dialog] button')].map(b => b.textContent.trim()).filter(Boolean)"
        )
        L("assistant buttons", btns)

    await step("assistant", asst())
    await ctx.close()


async def mobile(b):
    ctx = await b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=3, is_mobile=True, has_touch=True)
    pg = await ctx.new_page()
    await pg.goto(URL, wait_until="networkidle")
    await pg.wait_for_timeout(2500)
    await shot(pg, "m01_dashboard")
    await shot(pg, "m01_dashboard_full", True)
    open(f"{OUT}/m01.txt", "w", encoding="utf-8").write(await pg.inner_text("body"))
    await ctx.close()


async def main():
    run_live = "--live" in sys.argv
    async with async_playwright() as p:
        b = await p.chromium.launch()
        await desktop(b, run_live)
        await step("mobile", mobile(b))
        await b.close()


asyncio.run(main())
