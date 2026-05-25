"""Inspeciona estrutura da pagina ANP (seletores e tipo de CAPTCHA)."""
from __future__ import annotations

import asyncio
import re
from pathlib import Path

from patchright.async_api import async_playwright

URL = (
    "https://cdp.anp.gov.br/ords/r/cdp_apex/"
    "consulta-dados-publicos-cdp/base-de-distribuição-e-trr-autorizados-lista"
)
OUT = Path(__file__).resolve().parent.parent / "output" / "inspect"


async def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(locale="pt-BR", accept_downloads=True)
        page = await ctx.new_page()
        await page.goto(URL, wait_until="networkidle", timeout=120_000)
        await page.wait_for_timeout(3000)

        html = await page.content()
        (OUT / "page.html").write_text(html, encoding="utf-8")

        # Labels / selects
        for label in ["Tipo de Instalação", "Captcha", "Exportar"]:
            loc = page.get_by_text(label, exact=False)
            n = await loc.count()
            print(f"[label] {label!r}: {n} matches")

        selects = await page.locator("select").all()
        print(f"[select] total: {len(selects)}")
        for i, sel in enumerate(selects):
            name = await sel.get_attribute("name") or ""
            sid = await sel.get_attribute("id") or ""
            label = await sel.evaluate(
                """el => {
                    const l = el.closest('.t-Form-fieldContainer')?.querySelector('label');
                    return l ? l.innerText.trim() : '';
                }"""
            )
            opts = await sel.locator("option").all_text_contents()
            print(f"  select[{i}] id={sid!r} name={name!r} label={label!r} opts={opts[:4]}...")

        # Captcha hints
        for pat in [
            r"recaptcha",
            r"hcaptcha",
            r"cloudflare",
            r"turnstile",
            r"captcha",
            r"g-recaptcha",
        ]:
            if re.search(pat, html, re.I):
                print(f"[captcha-hint] found: {pat}")

        buttons = await page.locator("button, a.t-Button").all()
        print(f"[buttons] total: {len(buttons)}")
        for b in buttons[:30]:
            txt = (await b.inner_text()).strip().replace("\n", " ")
            if txt:
                print(f"  btn: {txt[:80]}")

        await page.screenshot(path=str(OUT / "screenshot.png"), full_page=True)
        await browser.close()
    print(f"Saved to {OUT}")


if __name__ == "__main__":
    asyncio.run(main())
