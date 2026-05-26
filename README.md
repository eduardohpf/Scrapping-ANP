# Scraper ANP CDP

Automatiza consultas públicas no [CDP da ANP](https://cdp.anp.gov.br/ords/r/cdp_apex/consulta-dados-publicos-cdp/home): resolve CAPTCHA de imagem Oracle APEX e exporta planilhas Excel.

## Pipelines

| Pipeline | Descrição | Comando |
|----------|-----------|---------|
| `br_anp_distribuicao_glp` (padrão) | Bases do ramo de liquefeitos | `python main.py` |
| `br_anp_posto_combustivel_revendedor` | Postos revendedores — exportar com tancagem | `python main.py --pipeline br_anp_posto_combustivel_revendedor` |

### Fluxo `br_anp_distribuicao_glp`

Acesso direto à lista, filtro **BASES DO RAMO DE LIQUEFEITOS**, botão **Exportar c/ todos os participantes**.

### Fluxo `br_anp_posto_combustivel_revendedor`

1. Home CDP → menu **SIMP** → **Consulta de Postos**
2. Filtro **POSTO REVENDEDOR** → CAPTCHA → **Exportar Com Tancagem**

## Estratégia anti-CAPTCHA

| Camada | Ferramenta | Função |
|--------|------------|--------|
| Navegação stealth | **Scrapling** `StealthySession` | patchright + flags anti-fingerprint |
| CAPTCHA | **ddddocr** (padrão) | OCR das 5 imagens por consulta |
| Retry | Refresh APEX | Até 8 tentativas |
| Fallback manual | `--no-headless --captcha-mode manual` | Digitação humana |
| Fallback API | `CAPTCHA_MODE=api` + `CAPTCHA_API_KEY` | 2Captcha |

## Estrutura do projeto

```
anp_scraper/
  pipelines/          # Specs por pipeline (URL, seletores, filtros)
  automation/       # Automação compartilhada + específica por pipeline
  captcha.py          # OCR / manual / 2Captcha (seletores parametrizados)
  config.py           # ScraperConfig
  scraper.py          # Orquestração Scrapling
  validators.py       # Validação do .xlsx
main.py               # CLI (--pipeline)
```

## Instalação e execução

```powershell
cd "c:\Users\eduar\OneDrive\Documentos\Scraping ANP"

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
scrapling install

python main.py
python main.py --pipeline br_anp_posto_combustivel_revendedor
```

### Opções úteis

```powershell
python main.py --no-headless --captcha-mode manual
python main.py --download-dir .\output\meus_dados
python main.py --log-level DEBUG

$env:ANP_PIPELINE = "br_anp_posto_combustivel_revendedor"
$env:CAPTCHA_MODE = "api"
$env:CAPTCHA_API_KEY = "sua_chave"
python main.py
```

## Saída esperada

- `br_anp_distribuicao_glp`: `output/downloads/` (ex. `exportação.xlsx`)
- `br_anp_posto_combustivel_revendedor`: `output/downloads/br_anp_posto_combustivel_revendedor/`
- Validação via openpyxl (tamanho, linhas, colunas)

## Aviso legal

Uso para consulta de dados públicos. Respeite os termos do portal ANP e a legislação aplicável.
