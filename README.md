# Scraper ANP CDP — Bases de Distribuição (Liquefeitos)

Automatiza a consulta pública da ANP, preenche o filtro **BASES DO RAMO DE LIQUEFEITOS**, resolve o CAPTCHA de imagem e exporta via **Exportar c/ todos os participantes**.

Portal: [Base de Distribuição e TRR Autorizados](https://cdp.anp.gov.br/ords/r/cdp_apex/consulta-dados-publicos-cdp/base-de-distribuição-e-trr-autorizados-lista)

## Estratégia anti-CAPTCHA

| Camada | Ferramenta | Função |
|--------|------------|--------|
| Navegação stealth | **Scrapling** `StealthySession` (patchright) | Reduz sinais de automação; `solve_cloudflare=False` (site não usa Cloudflare) |
| CAPTCHA | **ddddocr** (padrão) | OCR das 5 imagens do plugin Oracle APEX (`#anp_p25_captcha`) |
| Retry | Refresh APEX | Até 8 tentativas com nova imagem |
| Fallback manual | `--no-headless --captcha-mode manual` | Usuário digita o código no browser |
| Fallback API | `CAPTCHA_MODE=api` + `CAPTCHA_API_KEY` | 2Captcha para imagem base64 |

O Scrapling **não resolve** este CAPTCHA nativamente (`solve_cloudflare` cobre apenas Cloudflare Turnstile). A automação combina StealthySession + OCR dedicado.

## Estrutura do projeto

```
anp_scraper/
  config.py       # URL, seletores APEX, parâmetros
  captcha.py      # OCR / manual / 2Captcha
  automation.py   # Preenchimento, export, retries
  scraper.py      # Orquestração Scrapling
  validators.py   # Validação do .xlsx
main.py           # CLI
```

## Dependências

- Python 3.10+
- Pacotes em `requirements.txt`
- Browsers Scrapling: `scrapling install`

## Instalação e execução

```powershell
cd "c:\Users\eduar\OneDrive\Documentos\Teste Scrapling"

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
scrapling install

python main.py
```

### Opções úteis

```powershell
# Ver o navegador e digitar CAPTCHA manualmente
python main.py --no-headless --captcha-mode manual

# Pasta de download customizada
python main.py --download-dir .\output\meus_dados

# Logs detalhados
python main.py --log-level DEBUG

# 2Captcha (variáveis de ambiente)
$env:CAPTCHA_MODE = "api"
$env:CAPTCHA_API_KEY = "sua_chave"
python main.py
```

## Saída esperada

- Arquivo Excel em `output/downloads/` (nome sugerido pelo servidor, ex. `exportação.xlsx`)
- Validação: tamanho mínimo, leitura via openpyxl, contagem de linhas/colunas

## Seletores estáveis (Oracle APEX P25)

| Elemento | Seletor |
|----------|---------|
| Tipo de Instalação | `#P25_QUALIFICACAO` |
| CAPTCHA (imagens) | `#anp_p25_captcha img` |
| Entrada CAPTCHA | `#P25_CAPTCHA` |
| Refresh CAPTCHA | `#spn_captchaanp_refresh_anp_p25_captcha` |
| Exportar c/ participantes | `#B479395808106517986` |

## Aviso legal

Uso para consulta de dados públicos. Respeite os termos do portal ANP e a legislação aplicável.
