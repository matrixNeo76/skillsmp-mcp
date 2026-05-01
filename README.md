<div align="center">

# SkillsMP MCP Server

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://python.org)
[![Tests](https://github.com/matrixNeo76/skillsmp-mcp/actions/workflows/test.yml/badge.svg)](https://github.com/matrixNeo76/skillsmp-mcp/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.3.0-blue.svg)](VERSION)

**MCP server per cercare, confrontare e verificare skill AI su [SkillsMP.com](https://skillsmp.com).**
Integrazione nativa per Craft Agents. Cross-platform: Windows, macOS, Linux.

</div>

---

## Tools

| Tool | Descrizione |
|------|-------------|
| `skillsmp_search` | Keyword search con filtri (categoria, stelle, recente) |
| `skillsmp_ai_search` | AI semantic search (Cloudflare AI) |
| `skillsmp_check_skill` | Verifica se una skill locale esiste su SkillsMP |
| `skillsmp_compare_skills` | Confronta skill locale con alternative |
| `skillsmp_scan_domain` | Scansione di un intero dominio di skill |
| `skillsmp_refresh_structure` | Rigenera struttura skill dal filesystem locale |
| `skillsmp_status` | Mostra stato sistema (API, rate limit, cache) |
| `skillsmp_skill_diff` | Confronta contenuto locale vs SkillsMP |
| `skillsmp_check_outdated` | Report prioritizzato delle skill piu' obsolete |

Tutti i tool supportano `format="json"` per output machine-readable.

## Installazione Rapida

### Windows (PowerShell)
```powershell
git clone https://github.com/matrixNeo76/skillsmp-mcp.git
cd skillsmp-mcp
powershell -ExecutionPolicy Bypass -File setup.ps1
```

### Linux / macOS (Bash)
```bash
git clone https://github.com/matrixNeo76/skillsmp-mcp.git
cd skillsmp-mcp
bash setup.sh
```

### Manuale
```bash
pip install fastmcp httpx openpyxl
cp -r skills/skillsmp-checker ~/.agents/skills/
# Copia docs/mcp.example.json come ~/.mcp.json e aggiorna i path
export SKILLSMP_API_KEY="sk_live_..."
```

## Uso

```bash
# Verifica una skill locale
skillsmp_check_skill skill_name="stripe-integration"

# Scansiona un intero dominio
skillsmp_scan_domain domain_query="7. SECURITY"

# Confronta contenuto locale vs SkillsMP
skillsmp_skill_diff skill_name="fastapi-templates"

# Stato del sistema
skillsmp_status

# Output JSON
skillsmp_search q="react" format="json"
```

## Scripts

```bash
python scripts/generate_xlsx.py                              # Inventario XLSX
python scripts/generate_xlsx.py --with-skillsmp              # Con dati SkillsMP live
python scripts/generate_xlsx.py --csv                        # Esporta come CSV
python scripts/refresh_structure.py                          # Aggiorna struttura skill
python scripts/show_all_skills.py                            # Mostra skill verificate
```

## Struttura del Repository

```
skillsmp-mcp/
├── server.py                   # MCP server (9 tools)
├── VERSION                     # Versione corrente
├── setup.sh / setup.ps1        # Installer cross-platform
├── pyproject.toml              # Dipendenze Python
├── LICENSE                     # Apache 2.0
├── CHANGELOG.md                # Storico versioni
├── ARCHITECTURE.md             # Documentazione architetturale
├── CONTRIBUTING.md             # Guida ai contributi
├── AGENTS.md                   # Istruzioni per AI agent
├── SECURITY.md                 # Politiche di sicurezza
├── CODE_OF_CONDUCT.md          # Codice di condotta
├── README.md                   # Questo file
├── .gitignore
├── skills/
│   └── skillsmp-checker/
│       └── SKILL.md            # Skill per Craft Agents
├── data/
│   └── skill_structure.json    # 581 skill in 17 domini
├── tests/
│   └── test_server.py          # Suite di test (14 test)
├── scripts/
│   ├── refresh_structure.py    # Auto-scan filesystem
│   ├── generate_xlsx.py        # Genera XLSX/CSV
│   ├── show_all_skills.py      # Verifica bulk SkillsMP
│   └── install-hooks.ps1       # Pre-commit hook
├── .github/
│   └── workflows/
│       └── test.yml            # GitHub Actions CI
└── docs/
    ├── mcp.example.json        # Esempio configurazione MCP
    ├── guide.md                # Guida al source
    └── skillsmp-quickref.md    # Comandi rapidi
```

## Configurazione

Il server supporta un file `skillsmp-config.json` opzionale nella root del repo:
```json
{
  "cache_ttl": 300,
  "stable_ttl": 600,
  "max_retries": 3,
  "auto_refresh": true
}
```

## API Key

Ottieni una API key gratuita su [skillsmp.com](https://skillsmp.com).
- **500 richieste/giorno**, 30/minuto
- **Cache adattiva**: 5 min (default), 10 min (skill >1000 stelle)
- **Retry**: 3 tentativi con exponential backoff
- **Auto-refresh**: struttura skill sincronizzata all'avvio (saltata se <1 ora)

## Licenza

[Apache 2.0](LICENSE) — 2026 matrixNeo76
