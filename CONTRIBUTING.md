# Contribuire a SkillsMP MCP Server

Grazie per il tuo interesse! Ecco come contribuire.

## Prerequisiti

- Python 3.11+
- Git
- Conoscenza base di MCP (Model Context Protocol)

## Setup Sviluppo

```bash
git clone https://github.com/matrixNeo76/skillsmp-mcp.git
cd skillsmp-mcp
pip install -e .
pip install pytest  # per i test
```

## Linee Guida

### 1. Branch Strategy
- `main` — stabile, sempre rilasciabile
- `feature/*` — nuove funzionalità
- `fix/*` — bug fix
- `docs/*` — documentazione

### 2. Commit Messages
Usare [Conventional Commits](https://www.conventionalcommits.org/):
```
feat: add skillsmp_new_tool
fix: handle empty response in check_skill
docs: update README with examples
test: add tests for rate limiter
refactor: extract cache logic to module
```

### 3. Struttura del Codice
- `server.py` — solo tools MCP, niente logica di dominio qui
- `scripts/` — utility scripts, non MCP tools
- `data/` — file JSON generati, non modificare manualmente
- `tests/` — test corrispondenti 1:1 con i moduli

### 4. Aggiungere un Nuovo Tool MCP
1. Aggiungere funzione decorata con `@mcp.tool()` in `server.py`
2. Usare type hints per i parametri (FastMCP li usa per lo schema)
3. Supportare `format: str = "text"` per output JSON
4. Aggiungere test in `tests/test_server.py`
5. Aggiornare `AGENTS.md` con il nuovo tool
6. Aggiornare `CHANGELOG.md`

### 5. Modificare la Struttura Skill
Non modificare `data/skill_structure.json` direttamente:
```bash
python scripts/refresh_structure.py --merge
```

### 6. Test
```bash
python -m pytest tests/ -v
```
Tutti i test devono passare prima di fare PR.

### 7. Pre-commit Hook
```powershell
powershell -ExecutionPolicy Bypass -File scripts/install-hooks.ps1
```
Aggiorna automaticamente `skill_structure.json` prima di ogni commit.

## Processo di Release

1. Aggiornare `VERSION`
2. Aggiornare `CHANGELOG.md`
3. Commit: `chore: release vX.Y.Z`
4. Tag: `git tag -a vX.Y.Z -m "vX.Y.Z"`
5. Push: `git push && git push --tags`

## Segnalare Bug

Aprire una [issue](https://github.com/matrixNeo76/skillsmp-mcp/issues) con:
- Versione (da `VERSION`)
- Output del tool `skillsmp_status`
- Steps per riprodurre
- Comportamento atteso vs osservato

## Proporre Feature

Aprire una [discussione](https://github.com/matrixNeo76/skillsmp-mcp/discussions) o
una issue con label `enhancement` descrivendo:
- Il problema che risolve
- Come potrebbe funzionare
- Esempi d'uso
