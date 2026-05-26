"""Testa se exportação com apenas POSTO REVENDEDOR dispara download."""
from __future__ import annotations

import asyncio
from pathlib import Path

import ddddocr
from patchright.async_api import async_playwright

from anp_scraper.captcha import DdddOcrCaptchaSolver
from anp_scraper.pipelines.posto_revendedor import SELECTORS

URL = "https://cdp.anp.gov.br/ords/r/cdp_apex/consulta-dados-publicos-cdp/consulta-de-postos-lista"
OUT = Path(__file__).resolve().parent.parent / "output" / "downloads" / "br_anp_posto_combustivel_revendedor"


async def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    ocr = DdddOcrCaptchaSolver()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(locale="pt-BR", accept_downloads=True)
        page = await ctx.new_page()
        await page.goto(URL, wait_until="networkidle", timeout=120_000)
        await page.select_option(SELECTORS.primary_filter, value="1")
        for attempt in range(12):
            code = await ocr.solve_async(page, SELECTORS)
            print(f"attempt {attempt + 1}: {code!r}")
            if len(code) != 5:
                await page.locator(SELECTORS.captcha_refresh).click()
                await page.wait_for_timeout(1000)
                continue
            await page.locator(SELECTORS.captcha_input).fill(code)
            try:
                async with page.expect_download(timeout=300_000) as dl:
                    await page.locator(SELECTORS.export_button).click()
                d = await dl.value
                path = OUT / (d.suggested_filename or "test.xlsx")
                await d.save_as(path)
                print(f"OK: {path} ({path.stat().st_size} bytes)")
                break
            except Exception as exc:
                print(f"fail: {exc}")
                await page.wait_for_timeout(3000)
                for sel in ["#APEX_ERROR_MESSAGE", ".a-Notification-message", ".t-Alert-body"]:
                    loc = page.locator(sel)
                    if await loc.count():
                        txt = (await loc.first.inner_text()).strip()
                        if txt:
                            print(f"msg [{sel}]:", txt[:400])
                await page.locator(SELECTORS.captcha_refresh).click()
                await page.wait_for_timeout(1000)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
