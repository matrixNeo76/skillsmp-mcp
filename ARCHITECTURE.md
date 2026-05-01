# Architettura

## Panoramica

SkillsMP MCP Server è un server MCP (Model Context Protocol) che funge da ponte
tra **Craft Agents** e **SkillsMP.com**, un marketplace di skill per AI agent.

```
┌──────────────┐     MCP stdio     ┌──────────────────────┐     HTTPS     ┌──────────────┐
│ Craft Agent  │ ◄──────────────► │  skillsmp-mcp        │ ◄───────────► │ SkillsMP.com │
│ (sorgente)   │                  │  server.py (FastMCP)  │              │ REST API     │
│              │                  │                        │              │              │
│ 8 tools MCP  │                  │ - Rate limit tracker   │              │ /search      │
│              │                  │ - Cache adattiva       │              │ /ai-search   │
│              │                  │ - Retry con backoff    │              │ /health      │
└──────────────┘                  └──────────────────────┘              └──────────────┘
                                         │
                                         │ file system
                                         ▼
                                  ┌──────────────────────┐
                                  │  ~/.agents/skills/   │
                                  │  581 skill locali    │
                                  └──────────────────────┘
```

## Componenti

### 1. Server MCP (`server.py`)
- **Framework:** FastMCP 3.x (Python)
- **Strumenti:** 8 tools MCP
- **Trasporto:** stdio (comunicazione con Craft Agent)
- **Resilienza:** Exponential backoff (3 tentativi), rate limit tracking
- **Cache:** In-memory, TTL adattivo (5 min default, 10 min per skill stabili)
- **Auto-refresh:** Sincronizza struttura skill all'avvio

### 2. Struttura Dati (`data/skill_structure.json`)
- **Formato:** JSON centralizzato
- **Contenuto:** 581 skill organizzate in 17 domini
- **Categorizzazione:** Auto-categorizzazione per parola chiave
- **Sincronizzazione:** Refresh dal filesystem (`scripts/refresh_structure.py`)

### 3. Scripts Utility (`scripts/`)
| Script | Scopo |
|--------|-------|
| `refresh_structure.py` | Scansiona `.agents/skills/` e rigenera il JSON |
| `generate_xlsx.py` | Genera inventario XLSX/CSV con dati SkillsMP |
| `show_all_skills.py` | Verifica bulk tutte le skill su SkillsMP |
| `install-hooks.ps1` | Installa git pre-commit hook |

### 4. Skill per Craft Agent (`skills/skillsmp-checker/`)
- SKILL.md che sa quando attivarsi
- Trigger: "questa skill e' aggiornata?", "c'e' una skill migliore per X?"
- Usa i 8 tools MCP del source skillsmp

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

## Rate Limiting

| Parametro | Valore |
|-----------|--------|
| Limite giornaliero | 500 richieste |
| Limite minuto | 30 richieste |
| Cache default | 300 secondi |
| Cache skill stabili (>1000 stelle) | 600 secondi |
| Retry tentativi | 3 |
| Backoff | Esponenziale (2^n secondi) |

## Versionamento

La versione e' gestita dal file `VERSION` nella root del repo.
Ad ogni rilascio: aggiornare VERSION, CHANGELOG.md, e creare tag git.

## Test

- **Framework:** pytest
- **Copertura:** 14 test (rate limit, cache, formattazione, struttura)
- **CI:** GitHub Actions (Python 3.11, 3.12, 3.13)
- **Esecuzione:** `python -m pytest tests/ -v`
