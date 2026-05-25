"""Testa OCR no CAPTCHA da ANP."""
from __future__ import annotations

import asyncio
from io import BytesIO
from pathlib import Path

import ddddocr
from patchright.async_api import async_playwright
from PIL import Image

URL = (
    "https://cdp.anp.gov.br/ords/r/cdp_apex/"
    "consulta-dados-publicos-cdp/base-de-distribuição-e-trr-autorizados-lista"
)
OUT = Path(__file__).resolve().parent.parent / "output" / "captcha_test"


async def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    ocr = ddddocr.DdddOcr(show_ad=False)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(locale="pt-BR")
        page = await ctx.new_page()
        await page.goto(URL, wait_until="networkidle", timeout=120_000)
        await page.locator("#anp_p25_captcha img").first.wait_for(state="visible", timeout=60_000)

        imgs = page.locator("#anp_p25_captcha img")
        count = await imgs.count()
        print(f"images: {count}")
        chars = []
        for i in range(count):
            png = await imgs.nth(i).screenshot()
            (OUT / f"seg_{i}.png").write_bytes(png)
            text = ocr.classification(png)
            chars.append(text)
            print(f"  seg[{i}] -> {text!r}")

        combined = "".join(c for c in chars if c)
        print(f"combined: {combined!r}")

        # full container
        box_png = await page.locator("#anp_p25_captcha").screenshot()
        (OUT / "full.png").write_bytes(box_png)
        print(f"full OCR: {ocr.classification(box_png)!r}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
