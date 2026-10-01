import asyncio, sys
from playwright.async_api import async_playwright

OUT = sys.argv[1]
URL = "http://127.0.0.1:8510/"


def L(*a):
    print(*a, flush=True)


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


async def desktop(b):
    ctx = await b.new_context(viewport={"width": 1920, "height": 1080})
    pg = await ctx.new_page()
    await pg.goto(URL, wait_until="networkidle")
    await pg.wait_for_timeout(2000)

    async def spat():
        await nav(pg, "Spatial")
        await pg.get_by_label("Show synthetic demo scene (not real data)").check()
        await pg.wait_for_timeout(3000)
        x = pg.get_by_text("Scene layers").first
        await x.scroll_into_view_if_needed()
        await pg.evaluate("window.scrollBy(0,-160)")
        names = await pg.evaluate(
            "() => [...document.querySelectorAll('button')].map(b => (b.getAttribute('aria-label')||'') + '::' + b.textContent.trim()).filter(s => /section|plan|3d/i.test(s))"
        )
        L("spatial buttons", names)
        sec = pg.locator("button", has_text="section").first
        await sec.click()
        await pg.wait_for_timeout(2500)
        await shot(pg, "d15_spatial_EW_section")
        await pg.locator("button", has_text="3D model").first.click()
        await pg.wait_for_timeout(2500)
        await shot(pg, "d15_spatial_3D_model2")
        await pg.get_by_label("Show synthetic demo scene (not real data)").uncheck()
        await pg.wait_for_timeout(800)

    await step("spatial", spat())

    async def asst():
        await nav(pg, "Workspace")
        names = await pg.evaluate(
            "() => [...document.querySelectorAll('button')].map(b => (b.getAttribute('aria-label')||'') + '::' + b.textContent.trim()).filter(s => /assist|evidence|ask/i.test(s))"
        )
        L("assistant candidates", names)
        await pg.get_by_role("button", name="Open research assistant").first.click()
        await pg.wait_for_timeout(2000)
        await shot(pg, "d17_assistant_open")
        open(f"{OUT}/d17_assistant.txt", "w", encoding="utf-8").write(await pg.inner_text("body"))
        btns = await pg.evaluate(
            "() => [...document.querySelectorAll('button')].map(b => b.textContent.trim()).filter(t => t.length > 12 && t.length < 120)"
        )
        L("buttons", btns)
        # ask a grounded question through the visible prompt card or textbox
        asked = False
        for label in ["What does this result show", "Explain", "What phases", "magnetite", "Why"]:
            loc = pg.locator("button", has_text=label)
            if await loc.count():
                await loc.first.click()
                asked = True
                L("clicked prompt", label)
                break
        if not asked:
            box = pg.get_by_role("textbox").last
            await box.fill("Which phases were found in this result, and how reliable is it?")
            await box.press("Enter")
            L("typed question")
        await pg.wait_for_timeout(6000)
        await shot(pg, "d18_assistant_answer")
        open(f"{OUT}/d18_assistant.txt", "w", encoding="utf-8").write(await pg.inner_text("body"))

    await step("assistant", asst())
    await ctx.close()


async def mobile(b):
    ctx = await b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=3, is_mobile=True, has_touch=True)
    pg = await ctx.new_page()
    await pg.goto(URL, wait_until="networkidle")
    await pg.wait_for_timeout(2500)
    names = await pg.evaluate(
        "() => [...document.querySelectorAll('button,a')].map(b => (b.getAttribute('aria-label')||'') + '::' + b.textContent.trim()).filter(Boolean).slice(0,40)"
    )
    L("mobile buttons", names)
    for nm in ["Workspace", "Process", "Reports"]:
        try:
            await pg.get_by_role("button", name=nm, exact=True).first.click()
            await pg.wait_for_timeout(2200)
            await pg.evaluate("window.scrollTo(0,0)")
            await shot(pg, "m_" + nm)
            await shot(pg, "m_" + nm + "_full", True)
        except Exception as e:
            L("mobile fail", nm, repr(e)[:200])
    await ctx.close()


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        await desktop(b)
        await step("mobile", mobile(b))
        await b.close()


asyncio.run(main())
