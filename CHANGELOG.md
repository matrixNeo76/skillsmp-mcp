# Changelog

## v1.2.0 (2026-05-01)

### Added
- Nuovo tool: `skillsmp_skill_diff` — confronta contenuto locale vs SkillsMP
  (IDENTICA / SIMILE / DIVERSA con similarity score)
- Auto-refresh struttura all'avvio del server (--merge)
- Export CSV oltre a XLSX (flag `--csv` su generate_xlsx.py)
- Pre-commit hook per auto-refresh prima del commit
- File VERSION per gestione versioni centralizzata
- Link al repo GitHub nella SKILL.md

### Changed
- Versione server letta da file VERSION invece che hardcoded
- generate_xlsx.py ora funziona anche senza openpyxl (solo CSV)
- Struttura skill sempre sincronizzata all'avvio del server

## v1.1.0 (2026-05-01)

### Added
- 2 nuovi MCP tools: `skillsmp_refresh_structure` e `skillsmp_status`
- Auto-scan struttura skill da `.agents/skills/` con `scripts/refresh_structure.py`
- Output JSON su tutti i tools (parametro `format="json"`)
- Test suite con pytest (14 test)
- GitHub Actions CI workflow (Python 3.11, 3.12, 3.13)
- CHANGELOG.md

### Changed
- `show_all_skills.py` ora legge da `skill_structure.json` centralizzato
- `server.py` path relativi al repo (portabilità)
- `setup.ps1` e `setup.sh` idempotenti

### Fixed
- Disallineamento struttura JSON vs skill installate (581 skill sincronizzate)
- Path assoluti in `.mcp.json` sostituiti con path relativi al repo

## v1.0.0 (2026-05-01)

### Added
- MCP server con 5 tools: `skillsmp_search`, `skillsmp_ai_search`,
  `skillsmp_check_skill`, `skillsmp_compare_skills`, `skillsmp_scan_domain`
- Retry con exponential backoff (3 tentativi)
- Rate limit tracking (500/giorno)
- Cache adattiva (pattern stabili = cache piu lunga)
- `data/skill_structure.json` con 608 skill in 17 domini
- `scripts/generate_xlsx.py` per inventario XLSX
- Skill `skillsmp-checker` per Craft Agents
- Setup script per Windows (PowerShell) e Linux/macOS (Bash)
- Quick reference e guida al source
