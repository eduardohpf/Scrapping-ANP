"""Inspeciona estrutura da página SIMP / Consulta de postos (seletores APEX)."""
from __future__ import annotations

import asyncio
import re
from pathlib import Path

from patchright.async_api import async_playwright

URL = (
    "https://cdp.anp.gov.br/ords/r/cdp_apex/"
    "consulta-dados-publicos-cdp/home"
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
        (OUT / "home.html").write_text(html, encoding="utf-8")
        await page.screenshot(path=str(OUT / "home.png"), full_page=True)

        # SIMP dropdown
        for label in ["SIMP", "Consulta de postos", "POSTO REVENDEDOR", "Exportar com Tancagem"]:
            loc = page.get_by_text(label, exact=False)
            print(f"[text] {label!r}: {await loc.count()} matches")

        selects = await page.locator("select").all()
        print(f"[home selects] total: {len(selects)}")
        for i, sel in enumerate(selects):
            sid = await sel.get_attribute("id") or ""
            label = await sel.evaluate(
                """el => {
                    const l = el.closest('.t-Form-fieldContainer')?.querySelector('label');
                    return l ? l.innerText.trim() : '';
                }"""
            )
            opts = await sel.locator("option").all_text_contents()
            print(f"  select[{i}] id={sid!r} label={label!r} opts={opts[:6]}")

        # Try SIMP navigation
        try:
            simp = page.locator("select").filter(has=page.locator("option", has_text="Consulta de postos"))
            if await simp.count() == 0:
                # click by label
                for sel in selects:
                    opts = await sel.locator("option").all_text_contents()
                    if any("Consulta de postos" in o for o in opts):
                        await sel.select_option(label="Consulta de postos")
                        print("[nav] selected Consulta de postos via select")
                        break
            else:
                await simp.first.select_option(label="Consulta de postos")
                print("[nav] selected via filter")
        except Exception as exc:
            print(f"[nav] select failed: {exc}")

        await page.wait_for_timeout(5000)
        await page.screenshot(path=str(OUT / "after_nav.png"), full_page=True)
        (OUT / "after_nav.html").write_text(await page.content(), encoding="utf-8")

        selects2 = await page.locator("select").all()
        print(f"[after nav selects] total: {len(selects2)}")
        for i, sel in enumerate(selects2):
            sid = await sel.get_attribute("id") or ""
            label = await sel.evaluate(
                """el => {
                    const l = el.closest('.t-Form-fieldContainer')?.querySelector('label');
                    return l ? l.innerText.trim() : '';
                }"""
            )
            opts = await sel.locator("option").all_text_contents()
            print(f"  select[{i}] id={sid!r} label={label!r} opts={opts[:8]}")

        for pat in [r"anp_p\d+_captcha", r"P\d+_CAPTCHA", r"captcha"]:
            for m in re.findall(pat, await page.content(), re.I):
                if m not in ("captcha",):
                    print(f"[id-hint] {m}")

        buttons = await page.locator("button, a.t-Button").all()
        for b in buttons:
            txt = (await b.inner_text()).strip().replace("\n", " ")
            if txt and ("Exportar" in txt or "Tancagem" in txt or "posto" in txt.lower()):
                bid = await b.get_attribute("id") or ""
                print(f"  btn id={bid!r}: {txt[:80]}")

        await browser.close()
    print(f"Saved to {OUT}")


if __name__ == "__main__":
    asyncio.run(main())
