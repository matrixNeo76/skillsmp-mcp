# Changelog

Tutte le modifiche significative a questo progetto saranno documentate in questo file.

Il formato si basa su [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
e questo progetto aderisce al [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.1] — 2026-05-02

### Fixed
- `server.py`: versione hardcoded 1.2.0 → letta da VERSION file (era bloccata a 1.2.0)
- `import re` spostato in cima al file (era dentro funzione)
- `import subprocess` e `import csv` duplicati rimossi da funzioni
- `setup.sh` e `setup.ps1`: resi eseguibili (`chmod +x`)

### Added
- Supporto `.env` via `python-dotenv` (dipendenza opzionale)
- `server/utils.py` — modulo utilita' preparato per futuro refactoring
- 4 nuovi test: search JSON, check_outdated, discover categoria invalida, scan_domain inesistente
- `ANALYSIS_REPORT.md`: report completo codebase

### Changed
- `skills/skillsmp-checker/SKILL.md`: aggiornata con tabella completa 11 tools
- Test suite: da 23 a 27 test

## [1.4.0] — 2026-05-02

### Added
- **Nuovo tool:** `skillsmp_check_outdated` — report prioritizzato skill obsolete
- **Nuovo tool:** `skillsmp_discover` — scopri skill SkillsMP non installate
- **Nuovo tool:** `skillsmp_install_skill` — installa SKILL.md da GitHub
- **Cache persistente** su file (`data/cache_skillsmp.json`) tra sessioni
- **46 categorie SkillsMP** esplorabili via `skillsmp_discover`
- Export CSV da `skillsmp_check_outdated(save_csv=True)`
- Protezione batch in `generate_xlsx.py`: `--batch-size`, `--yes`, avviso preventivo

### Changed
- Test suite: da 19 a 23 test
- `show_all_skills.py`: potenziato con flag `--domain`, `--outdated`, `--format json`, `--limit`
- Auto-refresh: saltato se struttura ha <1 ora

## [1.3.0] — 2026-05-01

### Added
- **Nuovo tool:** `skillsmp_check_outdated` — scansiona tutte le skill e produce
  report prioritizzato delle piu' obsolete (parametri: domain, limit, min_stars)
- **Metadati struttura:** `skill_structure.json` ora include campo `_meta` con
  versione, timestamp ultimo refresh, conteggi
- **File di configurazione:** `skillsmp-config.json` opzionale per sovrascrivere
  cache_ttl, stable_ttl, max_retries, auto_refresh
- **19 test** (da 14) con integrazione per tools MCP (status, skill_diff, struttura)

### Changed
- `show_all_skills.py` potenziato: flag `--domain`, `--outdated`, `--format json`, `--limit`
- Auto-refresh all'avvio: saltato se struttura ha <1 ora
- ARCHITECTURE.md: aggiornata con 9 tools, configurazione, _meta
- README.md: aggiornato con 9 tools, configurazione

## [1.2.0] — 2026-05-01

### Added
- **Nuovo tool:** `skillsmp_skill_diff` — confronta contenuto SKILL.md locale vs SkillsMP
  con classificazione IDENTICA / SIMILE / DIVERSA e similarity score Jaccard
- **Auto-refresh struttura** all'avvio del server (merge con skill installate)
- **Export CSV** con flag `--csv` su `generate_xlsx.py` (funziona anche senza openpyxl)
- **Pre-commit hook** per auto-refresh di `skill_structure.json` prima del commit
- **File VERSION** per gestione versioni centralizzata
- **ARCHITECTURE.md** — documentazione architetturale completa
- **AGENTS.md** — istruzioni per AI agent che lavorano sul repo
- **CONTRIBUTING.md** — guida ai contributi con linee guida e processi
- **SECURITY.md** — politiche di sicurezza e gestione API key
- **CODE_OF_CONDUCT.md** — codice di condotta

### Changed
- `server.py`: versione letta da file `VERSION` invece che hardcoded
- `README.md`: completamente riscritto con badge, tool table, struttura aggiornata
- `generate_xlsx.py`: ora funziona in modalita' CSV anche senza openpyxl installato
- SKILL.md: aggiunto link al repository GitHub

## [1.1.0] — 2026-05-01

### Added
- **Nuovo tool:** `skillsmp_refresh_structure` — rigenera struttura skill da filesystem
- **Nuovo tool:** `skillsmp_status` — mostra stato sistema (API health, rate limit, cache)
- **Auto-scan struttura skill** con `scripts/refresh_structure.py --merge`
- **Output JSON** su tutti i tool (parametro `format="json"`)
- **Suite di test pytest** (14 test: rate limit, cache, formattazione, struttura)
- **GitHub Actions CI** (Python 3.11, 3.12, 3.13)
- `show_all_skills.py` ora legge da `skill_structure.json` centralizzato

### Changed
- `server.py`: path relativi al repo per portabilita'
- `setup.ps1` e `setup.sh`: ora idempotenti (ri-eseguibili senza danni)

### Fixed
- Disallineamento struttura JSON vs skill installate (581 skill sincronizzate)
- Path assoluti sostituiti con relativi

## [1.0.0] — 2026-05-01

### Added
- **MCP server** con 5 tools: `skillsmp_search`, `skillsmp_ai_search`,
  `skillsmp_check_skill`, `skillsmp_compare_skills`, `skillsmp_scan_domain`
- **Retry** con exponential backoff (3 tentativi)
- **Rate limit tracking** (500 richieste/giorno)
- **Cache adattiva**: 5 min (default), 10 min (skill con >1000 stelle)
- `data/skill_structure.json` con ~600 skill in 17 domini
- `scripts/generate_xlsx.py` per inventario XLSX
- Skill `skillsmp-checker` per Craft Agents
- Setup script per Windows (PowerShell) e Linux/macOS (Bash)
- Quick reference e guida al source
