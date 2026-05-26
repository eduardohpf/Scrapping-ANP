"""Inspeciona página consulta-de-postos-lista (P7)."""
from __future__ import annotations

import asyncio
import re
from pathlib import Path

from patchright.async_api import async_playwright

URL = (
    "https://cdp.anp.gov.br/ords/r/cdp_apex/"
    "consulta-dados-publicos-cdp/consulta-de-postos-lista"
)
OUT = Path(__file__).resolve().parent.parent / "output" / "inspect_postos"


async def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(locale="pt-BR", accept_downloads=True)
        page = await ctx.new_page()
        await page.goto(URL, wait_until="networkidle", timeout=120_000)
        await page.wait_for_timeout(3000)

        html = await page.content()
        (OUT / "postos_lista.html").write_text(html, encoding="utf-8")
        await page.screenshot(path=str(OUT / "postos_lista.png"), full_page=True)

        selects = await page.locator("select").all()
        print(f"[selects] {len(selects)}")
        for i, sel in enumerate(selects):
            sid = await sel.get_attribute("id") or ""
            label = await sel.evaluate(
                """el => {
                    const l = el.closest('.t-Form-fieldContainer')?.querySelector('label');
                    return l ? l.innerText.trim() : '';
                }"""
            )
            opts = await sel.locator("option").all_text_contents()
            print(f"  id={sid!r} label={label!r}")
            print(f"    opts={opts}")

        for pat in [r"#P\d+_\w+", r"anp_p\d+_captcha", r"spn_captcha"]:
            found = sorted(set(re.findall(pat, html, re.I)))
            print(f"[{pat}] {found[:20]}")

        buttons = await page.locator("button, a.t-Button").all()
        for b in buttons:
            txt = (await b.inner_text()).strip().replace("\n", " ")
            if txt and ("Exportar" in txt or "Tancagem" in txt or "Revendedor" in txt):
                bid = await b.get_attribute("id") or ""
                print(f"  btn id={bid!r}: {txt}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
