# Architettura

## Panoramica

SkillsMP MCP Server è un server MCP (Model Context Protocol) che funge da ponte
tra **Craft Agents** e **SkillsMP.com**, un marketplace di skill per AI agent.

```
┌──────────────┐     MCP stdio     ┌──────────────────────┐     HTTPS     ┌──────────────┐
│ Craft Agent  │ ◄──────────────► │  skillsmp-mcp        │ ◄───────────► │ SkillsMP.com │
│ (sorgente)   │                  │  server.py (FastMCP)  │              │ REST API     │
│              │                  │                        │              │              │
│ 9 tools MCP  │                  │ - Rate limit tracker   │              │ /search      │
│              │                  │ - Cache adattiva       │              │ /ai-search   │
│              │                  │ - Retry con backoff    │              │ /health      │
└──────────────┘                  └──────────────────────┘              └──────────────┘
                                         │
                                         │ file system
                                         ▼
                                  ┌──────────────────────┐
                                  │  ~/.agents/skills/   │
                                  │  580+ skill locali   │
                                  └──────────────────────┘
```

## Componenti

### 1. Server MCP (`server.py`)
- **Framework:** FastMCP 3.x (Python)
- **Strumenti:** 9 tools MCP
- **Trasporto:** stdio (comunicazione con Craft Agent)
- **Resilienza:** Exponential backoff (3 tentativi, configurabile), rate limit tracking
- **Cache:** In-memory, TTL adattivo (5 min default, 10 min per skill stabili, configurabile)
- **Auto-refresh:** Sincronizza struttura skill all'avvio (saltato se struttura <1 ora)
- **Config:** `skillsmp-config.json` opzionale per sovrascrivere default

### 2. Struttura Dati (`data/skill_structure.json`)
- **Formato:** JSON centralizzato con metadati (`_meta`)
- **Contenuto:** 580+ skill organizzate in 17 domini
- **Metadati:** Versione, timestamp ultimo refresh, conteggi
- **Sincronizzazione:** Refresh dal filesystem (`scripts/refresh_structure.py`)

### 3. Scripts Utility (`scripts/`)
| Script | Scopo |
|--------|-------|
| `refresh_structure.py` | Scansiona `.agents/skills/` e rigenera il JSON con `_meta` |
| `generate_xlsx.py` | Genera inventario XLSX/CSV con dati SkillsMP |
| `show_all_skills.py` | Verifica bulk con flag `--domain`, `--outdated`, `--format json` |
| `install-hooks.ps1` | Installa git pre-commit hook |

### 4. Skill per Craft Agent (`skills/skillsmp-checker/`)
- SKILL.md che sa quando attivarsi
- Trigger: "questa skill e' aggiornata?", "c'e' una skill migliore per X?"
- Usa i 9 tools MCP del source skillsmp

### 5. Configurazione MCP (`.mcp.json`)
- **Path:** `~/.mcp.json` (globale per tutti i workspace)
- **Auto-discovery:** Craft Agent rileva `.mcp.json` in HOME e nella root del progetto
- **Setup:** `setup.ps1` (Windows) o `setup.sh` (Linux/macOS)

## Flussi

### Flusso: Verifica Skill
```
User: "La skill stripe-integration e' aggiornata?"
  → SKILL.md match trigger
  → skillsmp_check_skill("stripe-integration")
    → server.py cerca su SkillsMP API
    → restituisce: stelle, data, autore
  → Output: "Trovata con 35K stelle, aggiornata 2026-04-14"
```

### Flusso: Scansione Dominio
```
User: "skillsmp_scan_domain('7. SECURITY')"
  → Legge struttura da skill_structure.json
  → Per ogni skill del dominio, chiama SkillsMP API
  → Restituisce tabella: nome | stelle | data | autore
```

### Flusso: Confronto Contenuto
```
User: "skillsmp_skill_diff('fastapi-templates')"
  → Legge SKILL.md locale
  → Cerca su SkillsMP
  → Confronta descrizioni (Jaccard similarity)
  → Output: IDENTICA / SIMILE / DIVERSA con score
```

### Flusso: Report Obsolete
```
User: "skillsmp_check_outdated(limit=10, min_stars=5000)"
  → Scansiona tutte le skill locali su SkillsMP
  → Filtra per stelle minime
  → Ordina per popolarità decrescente
  → Output: top 10 skill candidate a update
```

## Rate Limiting

| Parametro | Valore |
|-----------|--------|
| Limite giornaliero | 500 richieste |
| Limite minuto | 30 richieste |
| Cache default | 300 secondi (configurabile) |
| Cache skill stabili (>1000 stelle) | 600 secondi (configurabile) |
| Retry tentativi | 3 (configurabile) |
| Backoff | Esponenziale (2^n secondi) |
| Auto-refresh | All'avvio (saltato se struttura <1 ora) |
| Config file | skillsmp-config.json (opzionale) |

## Configurazione

File opzionale `skillsmp-config.json` nella root del repo:
```json
{
  "cache_ttl": 300,
  "stable_ttl": 600,
  "max_retries": 3,
  "auto_refresh": true
}
```

## Versionamento

La versione e' gestita dal file `VERSION` nella root del repo.
Ad ogni rilascio: aggiornare VERSION, CHANGELOG.md, e creare tag git.

## Test

- **Framework:** pytest
- **Copertura:** 19 test (utility + integrazione tools MCP)
- **CI:** GitHub Actions (Python 3.11, 3.12, 3.13)
- **Esecuzione:** `python -m pytest tests/ -v`

## Tools MCP (9)

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
| `skillsmp_discover` | Scopri skill SkillsMP che non hai |
| `skillsmp_install_skill` | Installa skill da GitHub |
