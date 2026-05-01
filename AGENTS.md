# AGENTS.md — Istruzioni per AI Agent

Questo file fornisce istruzioni a qualsiasi agente AI (Claude, GPT, Copilot, etc.)
che lavora su questo repository.

## Contesto

Questo repository contiene un **MCP server Python** per cercare, confrontare e
verificare skill AI su [SkillsMP.com](https://skillsmp.com). E' integrato con
**Craft Agents** tramite source MCP e skill dedicata.

## Struttura del Progetto

```
skillsmp-mcp/
├── server.py                   # MCP server principale (8 tools)
├── VERSION                     # Versione corrente (leggere da qui, non hardcodare)
├── data/
│   └── skill_structure.json    # 581 skill in 17 domini (auto-generato)
├── scripts/
│   ├── refresh_structure.py    # Scansiona .agents/skills/ e rigenera JSON
│   └── generate_xlsx.py        # Genera inventario XLSX/CSV
├── tests/
│   └── test_server.py          # 14 test pytest
└── skills/
    └── skillsmp-checker/
        └── SKILL.md            # Skill per Craft Agents
```

## Regole per l'Agente

### 1. Non modificare `data/skill_structure.json` manualmente
Il file e' auto-generato da `scripts/refresh_structure.py`. Per aggiornarlo:
```bash
python scripts/refresh_structure.py --merge
```

### 2. Versione da `VERSION`, non hardcodata
La versione del progetto e' nel file `VERSION`. Non hardcodare mai versioni.
```python
# ✅ Corretto
with open('VERSION') as f: version = f.read().strip()
# ❌ Sbagliato
version = "1.3.0"  # hardcoded
```

### 3. I test devono passare prima del push
```bash
python -m pytest tests/ -v
```

### 4. Struttura JSON centralizzata
Tutti gli script devono leggere/scrivere da `data/skill_structure.json`.
Non duplicare la struttura in piu' file.

### 5. Ogni rilascio richiede
1. Aggiornare `VERSION`
2. Aggiornare `CHANGELOG.md`
3. `git tag -a v<version> -m "v<version>"`
4. Pushare tutto (inclusi i tag)

## API SkillsMP

- **Base URL:** `https://skillsmp.com/api/v1`
- **Documentazione:** https://skillsmp.com/docs/api
- **API Key:** via env `SKILLSMP_API_KEY`
- **Rate limit:** 500 richieste/giorno

## Endpoints API

| Endpoint | Metodo | Descrizione |
|----------|--------|-------------|
| `/skills/search` | GET | Keyword search con filtri |
| `/skills/ai-search` | GET | AI semantic search |
| `/health` | GET | Health check |

## Build e Test

```bash
pip install -e .              # Installa dipendenze
python -m pytest tests/ -v    # Esegue test
python scripts/refresh_structure.py --merge  # Aggiorna struttura
python scripts/generate_xlsx.py              # Genera XLSX
python scripts/generate_xlsx.py --csv        # Genera CSV
```

## Strumenti MCP (8)

| Tool | Descrizione |
|------|-------------|
| `skillsmp_search` | Keyword search |
| `skillsmp_ai_search` | AI semantic search |
| `skillsmp_check_skill` | Verifica skill locale |
| `skillsmp_compare_skills` | Confronto con alternative |
| `skillsmp_scan_domain` | Scansione dominio |
| `skillsmp_refresh_structure` | Rigenera struttura |
| `skillsmp_status` | Stato sistema |
| `skillsmp_skill_diff` | Confronto contenuto |
| `skillsmp_check_outdated` | Report skill obsolete |
