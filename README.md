# SkillsMP MCP Server

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://python.org)

MCP server per cercare, confrontare e verificare skill AI su [SkillsMP.com](https://skillsmp.com).
Integrazione nativa per Craft Agents.

## Tools

| Tool | Descrizione |
|------|-------------|
| `skillsmp_search` | Keyword search con filtri (categoria, stelle, recente) |
| `skillsmp_ai_search` | AI semantic search (Cloudflare AI) |
| `skillsmp_check_skill` | Verifica se una skill locale esiste su SkillsMP |
| `skillsmp_compare_skills` | Confronta skill locale con alternative |
| `skillsmp_scan_domain` | Scansione di un intero dominio di skill |

Tutti i tool supportano `format="json"` per output machine-readable.

## Installazione Rapida

```bash
# 1. Clona il repo
git clone https://github.com/matrixNeo76/skillsmp-mcp.git
cd skillsmp-mcp

# 2. Esegui setup (installa skill + configura MCP)
bash setup.sh

# 3. Inserisci la tua API key SkillsMP quando richiesta
#    (ottienila su https://skillsmp.com)
```

## Installazione Manuale

```bash
# 1. Installa dipendenze
pip install fastmcp httpx openpyxl

# 2. Installa la skill
cp -r skills/skillsmp-checker ~/.agents/skills/

# 3. Configura MCP server (copia in ~/.mcp.json o nella root del progetto)
#    Vedi esempio in docs/mcp.example.json

# 4. Imposta API key
export SKILLSMP_API_KEY="sk_live_..."
```

## Struttura

```
skillsmp-mcp/
├── server.py                   ← MCP server (5 tools)
├── setup.sh                    ← Installer automatico
├── pyproject.toml              ← Dipendenze Python
├── README.md
├── .gitignore
├── skills/
│   └── skillsmp-checker/
│       └── SKILL.md            ← Skill per Craft Agents
├── data/
│   └── skill_structure.json    ← 608 skill in 17 domini
├── scripts/
│   ├── generate_xlsx.py        ← Genera inventario XLSX
│   └── show_all_skills.py      ← Mostra skill verificate
└── docs/
    ├── skillsmp-quickref.md    ← Comandi rapidi
    └── guide.md                ← Guida al source
```

## Scripts

```bash
# Genera XLSX base
python scripts/generate_xlsx.py

# Genera XLSX con dati SkillsMP (stelle, date, autore)
SKILLSMP_API_KEY="..." python scripts/generate_xlsx.py --with-skillsmp

# Mostra tutte le skill con verifica SkillsMP
SKILLSMP_API_KEY="..." python scripts/show_all_skills.py
```

## API Key

Ottieni una API key gratuita su [skillsmp.com](https://skillsmp.com).
- 500 richieste/giorno
- 30 richieste/minuto
- Cache adattiva integrata (5-10 min TTL)

## Licenza

Apache 2.0
