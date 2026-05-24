# Job Finder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Sistema Python que extrai dados do currículo em PDF, busca vagas LATAM/Brasil periodicamente em múltiplas fontes e salva análises de fit com score no Obsidian.

**Architecture:** Pipeline sequencial — parse do PDF → scraping de vagas em 3 fontes (Serper.dev/Google Jobs, Indeed, Himalayas) com Playwright humanizado → análise de fit via LLM (Ollama/llama3 ou GitHub Models/Claude Sonnet 4.6) → escrita de notas Markdown no vault do Obsidian com deduplicação por nome de arquivo.

**Tech Stack:** Python 3.11+, pdfplumber, playwright + playwright-stealth, openai SDK (compatível com Ollama e GitHub Models), requests, python-dotenv, python-slugify.

---

## Decisões de design (resumo da sessão grill-me)

| Decisão | Escolha |
|---|---|
| LLM | Configurável: `ollama` (llama3) ou `copilot` (claude-sonnet-4-6 via GitHub Models) |
| Auth Claude | `gh auth token` auto-detectado ou `COPILOT_TOKEN` no env |
| Fontes | Serper.dev (Google Jobs) → fallback Playwright; Indeed (Playwright); Himalayas (API REST) |
| Scraping | Playwright + playwright-stealth, delays aleatórios, simulação de mouse |
| Storage | Obsidian — uma nota `.md` por vaga + `Index.md` atualizado a cada run |
| Vault | `/Users/douglashennrich/Library/Mobile Documents/iCloud~md~obsidian/Documents/DHennrich/DHennrich/Job Finder` |
| Deduplicação | Verifica se o arquivo `.md` já existe no vault antes de processar |
| Score | 0-100 numérico + justificativa em texto + tier (🔥 ≥80, ✅ 60-79, 🤔 40-59, ❌ <40) |
| Threshold | Configurável via `.env` (`MIN_SCORE=60`) — vagas abaixo são descartadas |
| Index | Tabela Markdown simples (sem Dataview) atualizada a cada run |
| Agendamento | `launchd` — configurar somente após validação manual |

---

## File Structure

```
job-finder/
├── .env                        # variáveis de ambiente (não commitado)
├── .env.example                # template das variáveis
├── requirements.txt            # dependências Python
├── main.py                     # entry point — orquestra o pipeline completo
├── config.py                   # carrega .env, expõe Config dataclass tipada
├── resume/
│   ├── __init__.py
│   ├── profile.py              # dataclass Profile (raw_text + pdf_path)
│   └── parser.py               # extrai texto do PDF com pdfplumber
├── scrapers/
│   ├── __init__.py
│   ├── base.py                 # dataclass Job + interface BaseScraper (ABC)
│   ├── google_jobs.py          # Serper.dev primary + Playwright fallback
│   ├── indeed.py               # Playwright humanizado em indeed.com / indeed.com.br
│   └── himalayas.py            # API REST pública do himalayas.app
├── llm/
│   ├── __init__.py             # build_llm(config) factory
│   ├── base.py                 # interface BaseLLM (ABC) com método chat()
│   ├── ollama.py               # provider Ollama via openai SDK
│   └── copilot.py              # provider GitHub Models/Claude via openai SDK
├── analyzer.py                 # recebe Job + Profile, chama LLM, retorna JobAnalysis
└── obsidian/
    ├── __init__.py
    ├── templates.py            # render_job_note() + render_index()
    └── writer.py               # note_exists(), save_note(), update_index()
```

---

## Task 1: Scaffolding e configuração

**Files:**
- Create: `.env.example`
- Create: `requirements.txt`
- Create: `config.py`

- [ ] Criar `.env.example` com todas as variáveis documentadas:
  ```
  LLM_PROVIDER=copilot          # "copilot" | "ollama"
  COPILOT_TOKEN=                # auto-detectado via `gh auth token` se vazio
  COPILOT_MODEL=claude-sonnet-4-6
  OLLAMA_BASE_URL=http://localhost:11434/v1
  OLLAMA_MODEL=llama3
  SERPER_API_KEY=               # https://serper.dev — 2.500 queries gratuitas/mês
  OBSIDIAN_VAULT_PATH=/Users/douglashennrich/Library/Mobile Documents/iCloud~md~obsidian/Documents/DHennrich/DHennrich
  JOB_FINDER_FOLDER=Job Finder
  MIN_SCORE=60
  MAX_JOBS_PER_SOURCE=20
  ```
- [ ] Criar `requirements.txt`:
  ```
  pdfplumber==0.11.4
  playwright==1.44.0
  playwright-stealth==1.0.6
  openai==1.30.1
  requests==2.32.3
  python-dotenv==1.0.1
  python-slugify==8.0.4
  ```
- [ ] Criar `config.py` com `Config` dataclass que:
  - Carrega `.env` via `python-dotenv`
  - Auto-detecta `COPILOT_TOKEN` via `subprocess.run(["gh", "auth", "token"])` se não definido
  - Expõe `obsidian_job_folder` como `os.path.join(vault_path, job_finder_folder)`
- [ ] Copiar `.env.example` para `.env` e preencher `SERPER_API_KEY`
- [ ] Instalar dependências: `pip install -r requirements.txt`
- [ ] Instalar browser Playwright: `playwright install chromium`
- [ ] Verificar instalação: `python -c "import pdfplumber, playwright, openai; print('OK')"`

---

## Task 2: Resume module — parse do PDF

**Files:**
- Create: `resume/__init__.py`
- Create: `resume/profile.py`
- Create: `resume/parser.py`

- [ ] Criar `resume/profile.py`:
  ```python
  from dataclasses import dataclass

  @dataclass
  class Profile:
      raw_text: str
      pdf_path: str
  ```
- [ ] Criar `resume/parser.py` com `parse_pdf(pdf_path: str) -> Profile`:
  - Abre o PDF com `pdfplumber`
  - Extrai texto de todas as páginas (`page.extract_text()`)
  - Concatena com `\n\n` entre páginas
  - Levanta `FileNotFoundError` se o PDF não existir
- [ ] Smoke test manual:
  ```bash
  python -c "
  from resume.parser import parse_pdf
  p = parse_pdf('Douglas Hennrich.pdf')
  print(p.raw_text[:300])
  "
  ```
  Deve imprimir os primeiros 300 chars do texto extraído do PDF.

---

## Task 3: LLM providers

**Files:**
- Create: `llm/__init__.py`
- Create: `llm/base.py`
- Create: `llm/ollama.py`
- Create: `llm/copilot.py`

- [ ] Criar `llm/base.py` com `BaseLLM` (ABC) e método abstrato `chat(system: str, user: str) -> str`
- [ ] Criar `llm/ollama.py` com `OllamaLLM(base_url, model)`:
  - Usa `openai.OpenAI(base_url=base_url, api_key="ollama")`
  - `temperature=0.2` para respostas consistentes
- [ ] Criar `llm/copilot.py` com `CopilotLLM(token, model)`:
  - `base_url = "https://models.inference.ai.azure.com"`
  - `openai.OpenAI(base_url=..., api_key=token)`
  - `temperature=0.2`
- [ ] Criar `llm/__init__.py` com factory `build_llm(config: Config) -> BaseLLM`:
  - Se `config.llm_provider == "ollama"` → retorna `OllamaLLM`
  - Caso contrário → retorna `CopilotLLM` (levanta `RuntimeError` se token vazio)
- [ ] Smoke test (requer Ollama rodando ou token válido):
  ```bash
  # Copilot
  python -c "
  from config import Config
  from llm import build_llm
  cfg = Config.load()
  llm = build_llm(cfg)
  print(llm.chat('You are helpful.', 'Say hello in one word.'))
  "
  ```

---

## Task 4: Scrapers — base + Himalayas

**Files:**
- Create: `scrapers/__init__.py`
- Create: `scrapers/base.py`
- Create: `scrapers/himalayas.py`

- [ ] Criar `scrapers/base.py`:
  ```python
  from dataclasses import dataclass, field
  from typing import Optional
  from abc import ABC, abstractmethod

  @dataclass
  class Job:
      title: str
      company: str
      location: str
      description: str
      url: str
      source: str
      salary: Optional[str] = None
      posted_date: Optional[str] = None

  class BaseScraper(ABC):
      @abstractmethod
      def fetch(self, query: str, max_results: int) -> list[Job]: ...
  ```
- [ ] Criar `scrapers/himalayas.py` com `HimalayasScraper`:
  - GET `https://himalayas.app/jobs/api` com params `{"q": query, "limit": max_results}`
  - Mapeia campos JSON → `Job` dataclass
  - Filtra por `remote: true` e cargos LATAM/global
  - Captura exceções de rede com log de warning, retorna lista vazia em caso de erro
- [ ] Smoke test:
  ```bash
  python -c "
  from scrapers.himalayas import HimalayasScraper
  jobs = HimalayasScraper().fetch('nodejs nestjs react', 5)
  for j in jobs:
      print(j.title, '|', j.company)
  "
  ```

---

## Task 5: Scraper — Google Jobs via Serper.dev + fallback Playwright

**Files:**
- Create: `scrapers/google_jobs.py`

- [ ] Criar `scrapers/google_jobs.py` com `GoogleJobsScraper(api_key: str)`:

  **Primary — Serper.dev:**
  - POST `https://google.serper.dev/jobs`
  - Headers: `{"X-API-KEY": api_key, "Content-Type": "application/json"}`
  - Body: `{"q": query, "gl": "br", "hl": "pt-br", "num": max_results}`
  - Mapeia `jobs[]` da resposta JSON → `Job` dataclass
  - Campo `source = "google_jobs"`

  **Fallback Playwright** (chamado se Serper falhar ou `api_key` vazio):
  - Navega `https://www.google.com/search?q={query}&ibp=htl;jobs`
  - Usa stealth + delay aleatório de 2-4s entre ações
  - Extrai cards de vagas com seletor `div[data-ved] h3`
  - Limita ao `max_results` primeiros resultados

- [ ] Smoke test:
  ```bash
  python -c "
  from config import Config
  from scrapers.google_jobs import GoogleJobsScraper
  cfg = Config.load()
  jobs = GoogleJobsScraper(cfg.serper_api_key).fetch('senior fullstack nodejs nestjs remote LATAM', 5)
  for j in jobs:
      print(j.title, '|', j.company, '|', j.location)
  "
  ```

---

## Task 6: Scraper — Indeed com Playwright humanizado

**Files:**
- Create: `scrapers/indeed.py`

- [ ] Criar `scrapers/indeed.py` com `IndeedScraper`:
  - Usa `async playwright` com `playwright-stealth`
  - User-agent realista (Chrome/macOS)
  - Targets: `indeed.com` (global remote) e `indeed.com.br` (Brasil)
  - Search URL: `https://www.indeed.com/jobs?q={query}&remotejobs=1&sort=date`
  - Técnicas de humanização:
    - `random.uniform(1.5, 3.5)` de delay entre ações
    - `page.mouse.move()` com coordenadas aleatórias antes de clicar
    - Scroll gradual com `page.evaluate("window.scrollBy(0, {n})")`
  - Extrai: título (`.jobTitle`), empresa (`.companyName`), localização (`.companyLocation`), link (`.jcs-JobTitle`)
  - Para cada card, navega para a página da vaga para extrair `description` completa
  - Limita navegação de detalhe a `max_results` vagas

  > **Nota:** Indeed bloqueia headless browsers. Use `chromium.launch(headless=False)` durante testes. Após validação, mudar para `headless=True` com stealth ativo.

- [ ] Smoke test (abre browser visível):
  ```bash
  python -c "
  import asyncio
  from scrapers.indeed import IndeedScraper
  jobs = asyncio.run(IndeedScraper().fetch_async('senior fullstack developer nodejs', 3))
  for j in jobs:
      print(j.title, '|', j.company)
  "
  ```

---

## Task 7: Analyzer — LLM fit analysis

**Files:**
- Create: `analyzer.py`

- [ ] Criar `analyzer.py` com dataclass `JobAnalysis` e função `analyze(job, profile, llm) -> JobAnalysis`:

  **`JobAnalysis` dataclass:**
  ```python
  @dataclass
  class JobAnalysis:
      score: int            # 0-100
      tier: str             # "🔥 Must Apply" | "✅ Good Fit" | "🤔 Maybe" | "❌ Skip"
      justification: str    # 2-3 frases em pt-BR
      matching_skills: list[str]
      missing_skills: list[str]
  ```

  **System prompt:**
  ```
  You are an expert technical recruiter analyzing job fit for a software engineer candidate.
  Respond ONLY with a valid JSON object — no markdown, no explanation outside JSON.
  ```

  **User prompt:**
  ```
  CANDIDATE RESUME:
  {profile.raw_text}

  ---
  JOB POSTING:
  Title: {job.title}
  Company: {job.company}
  Location: {job.location}
  Description: {job.description}

  Analyze the fit and respond with:
  {
    "score": <integer 0-100>,
    "tier": "<🔥 Must Apply|✅ Good Fit|🤔 Maybe|❌ Skip>",
    "justification": "<2-3 sentences in Portuguese explaining score, highlighting matches and gaps>",
    "matching_skills": ["<skill>"],
    "missing_skills": ["<skill>"]
  }

  Scoring guide:
  80-100: Excellent fit — candidate has most required skills and experience level
  60-79:  Good fit — core skills match with minor gaps
  40-59:  Partial fit — relevant experience but significant gaps
  0-39:   Poor fit — major skill or seniority mismatch
  ```

  **Parsing:** `json.loads()` na resposta. Se falhar o parse, tentar extrair JSON com regex `\{.*\}` (re.DOTALL). Se ainda falhar, retornar `JobAnalysis(score=0, tier="❌ Skip", justification="Parse error", ...)`.

- [ ] Smoke test:
  ```bash
  python -c "
  from config import Config
  from llm import build_llm
  from resume.parser import parse_pdf
  from scrapers.base import Job
  from analyzer import analyze

  cfg = Config.load()
  llm = build_llm(cfg)
  profile = parse_pdf('Douglas Hennrich.pdf')
  job = Job(
      title='Senior NestJS Developer',
      company='Acme Corp',
      location='Remote LATAM',
      description='We need a senior backend developer with 5+ years in Node.js, NestJS, TypeScript, PostgreSQL, and Redis. Remote position open to LATAM candidates.',
      url='https://example.com/job/1',
      source='test'
  )
  result = analyze(job, profile, llm)
  print(f'Score: {result.score} | Tier: {result.tier}')
  print(f'Justification: {result.justification}')
  "
  ```

---

## Task 8: Obsidian module — templates + writer

**Files:**
- Create: `obsidian/__init__.py`
- Create: `obsidian/templates.py`
- Create: `obsidian/writer.py`

- [ ] Criar `obsidian/templates.py` com duas funções:

  **`render_job_note(job, analysis, date_str) -> str`** — gera o Markdown de uma nota de vaga:
  ```markdown
  ---
  score: {score}
  tier: "{tier}"
  company: {company}
  source: {source}
  date_found: {date}
  status: new
  ---

  # {title} — {company}

  {tier} **Score: {score}/100**

  > {justification}

  ## Skills
  - ✅ **Match:** {matching_skills joined by ", "}
  - ❌ **Gap:** {missing_skills joined by ", "}

  ## Details
  | Field | Value |
  |-------|-------|
  | Company | {company} |
  | Location | {location} |
  | Source | {source} |
  | Found | {date} |
  | Apply | [{url}]({url}) |

  ## Job Description
  {description}
  ```

  **`render_index(jobs_data: list[dict]) -> str`** — gera o `Index.md`:
  ```markdown
  # 🔍 Job Finder — Index

  *Last updated: {datetime}*

  ## 🔥 Must Apply (≥80)
  | Score | Title | Company | Source | Date | Note |
  |-------|-------|---------|--------|------|------|
  | ...   | ...   | ...     | ...    | ...  | [[link]] |

  ## ✅ Good Fit (60–79)
  | Score | Title | Company | Source | Date | Note |
  ...

  ## 🤔 Maybe (40–59)
  ...
  ```

- [ ] Criar `obsidian/writer.py` com funções:
  - `slugify_job(title, company) -> str` — ex: `"senior-nestjs-dev-acme-corp"`
  - `note_exists(slug, job_folder) -> bool` — checa se `{job_folder}/{slug}.md` existe
  - `save_note(slug, content, job_folder) -> str` — cria subpastas se necessário, escreve arquivo, retorna path
  - `update_index(job_folder, index_content) -> None` — sobrescreve `{job_folder}/Index.md`
  - `load_existing_jobs(job_folder) -> list[dict]` — lê frontmatter YAML de todas as notas existentes para reconstruir o Index

- [ ] Smoke test:
  ```bash
  python -c "
  from obsidian.writer import slugify_job, note_exists
  slug = slugify_job('Senior NestJS Developer', 'Acme Corp')
  print('Slug:', slug)
  "
  ```

---

## Task 9: main.py — pipeline completo

**Files:**
- Create: `main.py`

- [ ] Criar `main.py` que orquestra o pipeline:

  ```python
  # Pseudocódigo do pipeline
  config = Config.load()
  llm = build_llm(config)
  profile = parse_pdf("Douglas Hennrich.pdf")

  scrapers = [
      GoogleJobsScraper(config.serper_api_key),
      IndeedScraper(),
      HimalayasScraper(),
  ]

  QUERIES = [
      "senior fullstack developer nodejs nestjs typescript react remote LATAM",
      "desenvolvedor fullstack senior nodejs react typescript remoto Brasil",
  ]

  all_jobs = []
  for scraper in scrapers:
      for query in QUERIES:
          jobs = scraper.fetch(query, config.max_jobs_per_source)
          all_jobs.extend(jobs)

  # Deduplicar pelo slug antes de processar
  seen_slugs = set()
  unique_jobs = []
  for job in all_jobs:
      slug = slugify_job(job.title, job.company)
      if slug not in seen_slugs:
          seen_slugs.add(slug)
          unique_jobs.append(job)

  saved = 0
  skipped_dup = 0
  skipped_score = 0

  for job in unique_jobs:
      slug = slugify_job(job.title, job.company)

      # Deduplicação no vault
      if note_exists(slug, config.obsidian_job_folder):
          skipped_dup += 1
          continue

      analysis = analyze(job, profile, llm)

      if analysis.score < config.min_score:
          print(f"[SKIP] {job.title} @ {job.company} — Score {analysis.score} < {config.min_score}")
          skipped_score += 1
          continue

      note = render_job_note(job, analysis, today)
      save_note(slug, note, config.obsidian_job_folder)
      saved += 1
      print(f"[SAVED] {analysis.tier} {job.title} @ {job.company} — Score {analysis.score}")

  # Atualiza Index.md com todas as notas existentes
  all_existing = load_existing_jobs(config.obsidian_job_folder)
  update_index(config.obsidian_job_folder, render_index(all_existing))

  print(f"\nDone. Saved: {saved} | Skipped (dup): {skipped_dup} | Skipped (score): {skipped_score}")
  ```

- [ ] Testar pipeline completo manualmente:
  ```bash
  COPILOT_TOKEN="$(gh auth token)" python main.py
  ```
- [ ] Verificar no Obsidian que as notas aparecem em `Job Finder/`
- [ ] Verificar que `Index.md` foi criado/atualizado corretamente

---

## Task 10: launchd — agendamento (após validação)

> ⚠️ **Executar somente após confirmar que o pipeline funciona corretamente.**

**Files:**
- Create: `com.douglashennrich.jobfinder.plist`

- [ ] Criar o plist do launchd:
  ```xml
  <?xml version="1.0" encoding="UTF-8"?>
  <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" ...>
  <plist version="1.0">
  <dict>
      <key>Label</key>
      <string>com.douglashennrich.jobfinder</string>
      <key>ProgramArguments</key>
      <array>
          <string>/usr/bin/python3</string>
          <string>/Users/douglashennrich/Documents/Projetos/job-finder/main.py</string>
      </array>
      <key>EnvironmentVariables</key>
      <dict>
          <key>COPILOT_TOKEN</key>
          <string><!-- será populado pelo script de instalação --></string>
      </dict>
      <key>StartCalendarInterval</key>
      <array>
          <dict><key>Hour</key><integer>9</integer><key>Minute</key><integer>0</integer></dict>
          <dict><key>Hour</key><integer>18</integer><key>Minute</key><integer>0</integer></dict>
      </array>
      <key>WorkingDirectory</key>
      <string>/Users/douglashennrich/Documents/Projetos/job-finder</string>
      <key>StandardOutPath</key>
      <string>/Users/douglashennrich/Documents/Projetos/job-finder/logs/job-finder.log</string>
      <key>StandardErrorPath</key>
      <string>/Users/douglashennrich/Documents/Projetos/job-finder/logs/job-finder-error.log</string>
  </dict>
  </plist>
  ```
- [ ] Script de instalação `install_launchd.sh`:
  ```bash
  #!/bin/bash
  TOKEN=$(gh auth token)
  PLIST="$HOME/Library/LaunchAgents/com.douglashennrich.jobfinder.plist"
  # substitui o token no plist e copia para LaunchAgents
  sed "s/<!-- será populado pelo script de instalação -->/$TOKEN/" \
      com.douglashennrich.jobfinder.plist > "$PLIST"
  launchctl load "$PLIST"
  echo "Job Finder agendado para rodar às 9h e 18h."
  ```
- [ ] Testar: `launchctl start com.douglashennrich.jobfinder`
- [ ] Verificar logs: `tail -f logs/job-finder.log`

---

## Ordem de execução recomendada

```
Task 1 → Task 2 → Task 3 → Task 4 → Task 5 → Task 6 → Task 7 → Task 8 → Task 9
```

Task 10 somente após Task 9 validada manualmente.

Tasks 4, 5 e 6 (scrapers) podem ser desenvolvidas em paralelo após Task 1-3 concluídas.

---

## Variáveis de ambiente necessárias

| Variável | Obrigatória | Como obter |
|---|---|---|
| `SERPER_API_KEY` | Sim (para Google Jobs) | https://serper.dev — cadastro gratuito |
| `COPILOT_TOKEN` | Se `LLM_PROVIDER=copilot` | `gh auth token` (auto-detectado) |
| `OBSIDIAN_VAULT_PATH` | Sim | Caminho local do vault |
| `MIN_SCORE` | Não (default: 60) | Ajustar conforme volume |
| `MAX_JOBS_PER_SOURCE` | Não (default: 20) | Ajustar conforme performance |

---

## Notas de segurança

- `.env` no `.gitignore` (nunca commitar token ou API key)
- `COPILOT_TOKEN` é efêmero — renovar via `gh auth token` a cada uso ou no plist via script
- Playwright roda localmente — nenhuma credencial trafega para servidores externos além do LLM e Serper.dev
- Serper.dev só recebe queries de texto — nenhum dado do currículo é enviado
