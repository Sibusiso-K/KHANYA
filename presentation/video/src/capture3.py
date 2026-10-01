import asyncio, sys
from playwright.async_api import async_playwright

OUT = sys.argv[1]
URL = "http://127.0.0.1:8510/"


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={"width": 1920, "height": 1080}, device_scale_factor=2)
        pg = await ctx.new_page()
        await pg.goto(URL, wait_until="networkidle")
        await pg.wait_for_timeout(2000)
        # logo mark: first svg/img inside the brand link
        brand = pg.locator("header a").first
        await brand.screenshot(path=f"{OUT}/hi_brand.png")
        colors = await pg.evaluate("""() => {
          const pick = (sel) => { const e = document.querySelector(sel); if (!e) return null; const s = getComputedStyle(e); return {bg: s.backgroundColor, fg: s.color, font: s.fontFamily}; };
          const run = [...document.querySelectorAll('button')].find(b => /Run analysis|Inspect specimen/.test(b.textContent));
          const rs = run ? getComputedStyle(run) : null;
          return {body: pick('body'), h1: pick('h1'), run: rs ? {bg: rs.backgroundColor, font: rs.fontFamily} : null};
        }""")
        print(colors)
        await pg.get_by_role("button", name="Workspace", exact=True).first.click()
        await pg.wait_for_timeout(2500)
        for mode in ["Original", "Phase overlay", "Phase mask"]:
            await pg.get_by_role("button", name=mode, exact=True).first.click()
            await pg.wait_for_timeout(1500)
            img = pg.locator("img").filter(has_not_text="").nth(0)
            # screenshot the viewer stage region: find the largest visible img
            box = await pg.evaluate("""() => {
              const imgs = [...document.querySelectorAll('img, canvas')].filter(i => i.getBoundingClientRect().width > 400);
              imgs.sort((a, b) => b.getBoundingClientRect().width * b.getBoundingClientRect().height - a.getBoundingClientRect().width * a.getBoundingClientRect().height);
              const r = imgs[0].getBoundingClientRect(); return {x: r.x, y: r.y, w: r.width, h: r.height};
            }""")
            print(mode, box)
            await pg.screenshot(path=f"{OUT}/hi_view_{mode.replace(' ', '_')}.png",
                                clip={"x": box["x"], "y": box["y"], "width": box["w"], "height": box["h"]})
        await b.close()


asyncio.run(main())
