import re
from pathlib import Path

h = Path("output/inspect_postos/home.html").read_text(encoding="utf-8")
for m in re.finditer(r"<a href=\"([^\"]+)\"[^>]*>([^<]+)</a>", h):
    if "posto" in m.group(2).lower() or "posto" in m.group(1).lower():
        print(m.group(2), "->", m.group(1))
