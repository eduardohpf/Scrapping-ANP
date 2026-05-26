"""Verifica mensagens APEX após export com só POSTO REVENDEDOR."""
from __future__ import annotations

import asyncio

from patchright.async_api import async_playwright

URL = "https://cdp.anp.gov.br/ords/r/cdp_apex/consulta-dados-publicos-cdp/consulta-de-postos-lista"


async def main() -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await (await browser.new_context(locale="pt-BR")).new_page()
        await page.goto(URL, wait_until="networkidle", timeout=120_000)
        await page.select_option("#P7_TIPO_POSTO", value="1")
        await page.locator("#P7_CAPTCHA_1").fill("AAAAA")
        await page.locator("#B627337254132141370").click()
        await page.wait_for_timeout(5000)
        print("body text:", (await page.locator(".t-Alert-body").inner_text())[:800])
        print("notification:", (await page.locator(".a-Notification-message").all_inner_texts()))
        errs = await page.locator(".a-Form-error:visible").all_inner_texts()
        print("form errors:", errs)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
