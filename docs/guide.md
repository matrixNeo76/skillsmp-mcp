# SkillsMP Source — Guida all'Uso (v2)

SkillsMP e un marketplace di skill per AI agent. Questo source espone 5 tools
per cercare, confrontare e verificare skill su skillsmp.com.

## Tools Disponibili

### 1. `skillsmp_search` — Ricerca Keyword
Parametri: `q` (req), `category`, `sort_by`, `limit`, `format` (text/json)
Quando: scoprire skill popolari o recenti su un argomento.

### 2. `skillsmp_ai_search` — Ricerca Semantica AI
Parametri: `q` (req), `format` (text/json)
Quando: descrivere cosa vuoi fare in linguaggio naturale.

### 3. `skillsmp_check_skill` — Verifica Skill Locale
Parametri: `skill_name` (req), `author_hint`, `format` (text/json)
Quando: verificare se la skill locale ha corrispondenze aggiornate su SkillsMP.

### 4. `skillsmp_compare_skills` — Confronto Skill
Parametri: `skill_name` (req), `local_stars`, `format` (text/json)
Quando: decidere se la skill locale e ancora la scelta migliore.

### 5. `skillsmp_scan_domain` — Scansione Dominio (NUOVO)
Parametri: `domain_query` (req, es. "7. SECURITY"), `format` (text/json)
Quando: scansionare un intero dominio di skill su SkillsMP in una volta sola.

## Pattern d'Uso

**Verifica singola:** skillsmp_check_skill("stripe-integration")
**Confronto:** skillsmp_compare_skills("fastapi-templates")
**Scansione dominio:** skillsmp_scan_domain("7. SECURITY")
**Ricerca JSON:** skillsmp_search(q="react", format="json")
**AI search:** skillsmp_ai_search("How to build a web scraper")

## Note
- Rate limit: 500 req/giorno, 30/min
- Cache adattiva: 5-10 minuti
- Output JSON disponibile su tutti i tool
- Struttura skill centralizzata in craft-memory/data/skill_structure.json
- XLSX inventory in craft-memory/docs/skill_inventory.xlsx
