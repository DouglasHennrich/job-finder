# Limitações Conhecidas — Job Finder

Documento de referência com limitações operacionais e técnicas descobertas durante o desenvolvimento e validação do pipeline.

---

## T025 — GoogleJobsScraper: sem resultados

**Sintoma:** `GoogleJobsScraper` retorna 0 vagas em ambas as queries.

### Causa 1 — Serper.dev sem plano Jobs API

```
GoogleJobsScraper Serper failed: 404 Client Error: Not Found
URL: https://google.serper.dev/jobs
```

A chave `SERPER_API_KEY` configurada no `.env` pertence ao plano gratuito do Serper.dev, que **não inclui o endpoint `/jobs`**. Os endpoints disponíveis no free tier são `/search` (web), `/news` e `/images`.

**Impacto:** O caminho primário do scraper sempre falha. O código degrada para o fallback Playwright.

**Solução:** Assinar o plano "Jobs API" do Serper.dev, ou substituir pelo endpoint de busca web + parsing de resultados orgânicos do Google.

### Causa 2 — Playwright bloqueado por bot detection do Google

O fallback usa Playwright headless para acessar `https://www.google.com/search?q=...&ibp=htl;jobs`. O Google detecta o scraping e retorna 0 resultados (ou CAPTCHA).

- Seletor `div[data-jiz]` pode estar stale (Google altera a estrutura do DOM frequentemente).
- Playwright com `playwright-stealth` não é suficiente para o Google Jobs especificamente.

**Impacto:** Fonte de vagas completamente inoperante.

**Possíveis soluções:**
- Usar a [Google Custom Search JSON API](https://developers.google.com/custom-search/v1/overview) com filtro de site `site:linkedin.com/jobs OR site:himalayas.app`.
- Integrar diretamente a [SerpAPI](https://serpapi.com/) (paga, mas confiável).
- Substituir `GoogleJobsScraper` por outro scraper (e.g., Remotive, WeWorkRemotely).

---

## LLM — Rate Limit do GitHub Models (provider `copilot`)

**Sintoma:** Pipeline crasha na fase de scoring após ~10 vagas.

```
openai.RateLimitError: 429 - Rate limit of 50 per 86400s exceeded for UserByModelByDay.
```

O plano free do **GitHub Models** (`models.inference.ai.azure.com`) limita a **50 requests por modelo por dia**. Uma sessão de debug com 30 vagas esgota a cota em minutos.

**Modelos afetados:** `gpt-4o`, `claude-sonnet-4.6` (indisponível neste endpoint), e demais modelos do catálogo free.

**Status do código:** O erro é capturado graciosamente desde o fix — o pipeline para o scoring early, salva as vagas já processadas, atualiza o `Index.md` e encerra com `exit 0` (antes crashava com `exit 1`).

**Soluções:**
- Usar Ollama local (sem rate limit) — ver seção abaixo.
- Assinar GitHub Copilot Pro / Enterprise para limites maiores.
- Adicionar `time.sleep()` entre chamadas para espaçar o uso diário.

---

## LLM — Qualidade de scoring com Ollama (`llama3`)

**Sintoma:** Scores inflados e incorretos. Vagas completamente irrelevantes recebem 85/100 🔥.

Comparação para as mesmas vagas:

| Vaga | `gpt-4o` | `llama3` |
|------|---------|---------|
| Spanish-Speaking Cybersecurity Agent | 20 ❌ | 85 🔥 |
| AI Enablement Intern | 40 🤔 | 85 🔥 |
| Project Manager (talent pool) | 30 ❌ | 85 🔥 |
| Senior Specialty Consultative Pharmacist | 0 ❌ | 60 ✅ |
| Spanish Interpreter | 10 ❌ | 60 ✅ |

O `llama3` não segue o prompt de sistema com fidelidade suficiente para avaliação criteriosa. Tende a retornar JSON com scores altos independente do fit real.

**Recomendação:** Para scoring confiável, usar `gpt-4o` (GitHub Models, dentro da cota diária) ou testar `qwen2.5-coder:latest` do Ollama com ajuste do system prompt.

---

## IndeedScraper — Queries em Português retornam 0 vagas

**Sintoma:** `IndeedScraper | 'desenvolvedor fullstack senior nodejs react remoto' → 0 jobs`

O Indeed (domínio `.com`) indexa majoritariamente vagas em inglês. Queries em português não retornam resultados relevantes no `indeed.com`.

**Impacto:** Metade das queries (o par em PT-BR) é desperdiçada no Indeed.

**Solução:** Restringir IndeedScraper para queries em inglês, ou adicionar suporte ao `br.indeed.com` com queries em português.

---

## launchd — Configuração necessária no macOS

Ao rodar o pipeline via `launchd` (scheduler), foram necessárias as seguintes configurações não óbvias:

### 1. `PYTHONUNBUFFERED=1` obrigatório

Sem esta variável de ambiente no plist, o stdout do Python é bufferizado em bloco quando não há TTY. Os arquivos de log ficam em 0 bytes até o processo encerrar (ou nunca aparecem se o processo travar).

```xml
<key>EnvironmentVariables</key>
<dict>
  <key>PYTHONUNBUFFERED</key>
  <string>1</string>
</dict>
```

### 2. Python do venv, não do sistema

O executável deve ser `.venv/bin/python` e não `/usr/bin/python3`. O Python do sistema não tem acesso ao venv e falha ao importar as dependências.

### 3. Full Disk Access (FDA) para Python

No macOS, `launchd` roda sob restrições TCC mais rígidas. O Python do venv (binário em `/opt/homebrew/`) ficava travado em `_PyConfig_InitPathConfig → fopen` sem o **Full Disk Access** concedido em:

> **System Settings → Privacy & Security → Full Disk Access** → adicionar o binário Python do Homebrew.

Sem FDA, o processo inicia (PID alocado) mas não produz nenhuma saída e nunca avança além da inicialização do interpretador.

---

## Python 3.14 — Breaking change no asyncio

**Sintoma:**
```
DeprecationWarning / RuntimeError: no current event loop
```

Em Python 3.14, `asyncio.get_event_loop().run_until_complete(coro)` foi removido em contextos sem loop ativo. Todo código que executava corrotinas a partir de código síncrono precisou ser atualizado para `asyncio.run(coro)`.

**Arquivos afetados:** `scrapers/google_jobs.py`, `scrapers/indeed.py`.

---

## playwright-stealth v2 — API quebrada

A versão `2.x` do pacote `playwright-stealth` removeu a função `stealth_async`:

```python
# v1 (quebrado na v2)
from playwright_stealth import stealth_async
await stealth_async(page)

# v2 (correto)
from playwright_stealth import Stealth
await Stealth().apply_stealth_async(page)
```

**Versão instalada:** `playwright-stealth==2.0.3`

---

## Dedup — Company name ausente gera slugs genéricos

Algumas vagas (especialmente do Indeed) não expõem o nome da empresa. O campo `company` fica vazio (`""`), gerando slugs como `senior-full-stack-software-engineer` (sem empresa), o que pode colidir com outra vaga de título idêntico de empresa diferente.

**Impacto:** Pequeno risco de vaga não ser salva (dedup falso positivo) ou nota sobrescrita.

**Solução:** Fallback no slug: se `company` vazio, incluir hash dos primeiros 8 chars da URL ou do título completo.
