"""Teste fluxo completo: filtro + captcha + export."""
from __future__ import annotations

import asyncio
import re
from pathlib import Path

import ddddocr
from patchright.async_api import async_playwright

URL = (
    "https://cdp.anp.gov.br/ords/r/cdp_apex/"
    "consulta-dados-publicos-cdp/base-de-distribuição-e-trr-autorizados-lista"
)
DOWNLOAD_DIR = Path(__file__).resolve().parent.parent / "output" / "downloads"
INSTALLATION_VALUE = "3"  # BASES DO RAMO DE LIQUEFEITOS


def solve_captcha_png(png: bytes, ocr: ddddocr.DdddOcr) -> str:
    text = ocr.classification(png)
    return re.sub(r"[^a-zA-Z0-9]", "", text)[:5]


async def read_captcha(page, ocr: ddddocr.DdddOcr) -> str:
    await page.locator("#anp_p25_captcha img").first.wait_for(state="visible", timeout=30_000)
    imgs = page.locator("#anp_p25_captcha img")
    parts = []
    for i in range(await imgs.count()):
        png = await imgs.nth(i).screenshot()
        parts.append(solve_captcha_png(png, ocr))
    combined = "".join(parts)
    if len(combined) >= 4:
        return combined[:5]
    full = await page.locator("#anp_p25_captcha").screenshot()
    return solve_captcha_png(full, ocr)


async def main() -> None:
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    ocr = ddddocr.DdddOcr(show_ad=False)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(locale="pt-BR", accept_downloads=True)
        page = await ctx.new_page()
        await page.goto(URL, wait_until="networkidle", timeout=120_000)
        await page.wait_for_selector("#P25_QUALIFICACAO", state="visible")

        await page.select_option("#P25_QUALIFICACAO", value=INSTALLATION_VALUE)
        await page.wait_for_timeout(500)

        for attempt in range(5):
            code = await read_captcha(page, ocr)
            print(f"attempt {attempt + 1}: captcha={code!r}")
            await page.locator("#P25_CAPTCHA").fill(code)

            async with page.expect_download(timeout=120_000) as dl_info:
                await page.locator("#B479395808106517986").click()
            try:
                download = await dl_info.value
                path = DOWNLOAD_DIR / download.suggested_filename
                await download.save_as(path)
                print(f"OK download: {path} ({path.stat().st_size} bytes)")
                break
            except Exception as exc:
                print(f"download failed: {exc}")
                err = page.locator(".a-Notification-message, .t-Alert-body")
                if await err.count():
                    print("alert:", await err.first.inner_text())
                await page.locator("#spn_captchaanp_refresh_anp_p25_captcha").click()
                await page.wait_for_timeout(1500)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
