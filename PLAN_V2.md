# SkillsMP MCP — Analisi e Piano Miglioramenti v2

> Data: 2026-05-01
> Stato attuale: 13 files, 605 righe server.py, 5 tools

---

## 1. Criticità Identificate (9)

### 🔴 Criticità 1: Skill structure disallineata
**Problema:** Lo `skill_structure.json` è hardcoded e manuale. Attualmente ci sono **39 skill installate** nel sistema che non sono nel file JSON.
**Impatto:** Alto — lo scan_domain non vede skill reali
**Fix:** Aggiungere comando/tool che scansiona `.agents/skills/` e rigenera il JSON

### 🔴 Criticità 2: Path assoluto in .mcp.json
**Problema:** Il path a `server.py` è assoluto (`C:/Users/.../repos/skillsmp-mcp/server.py`). Se sposti il repo, il MCP server si rompe.
**Impatto:** Alto — portabilità ridotta
**Fix:** Aggiungere supporto a variabili `${REPO_DIR}` o rendere setup.ps1/setup.sh idempotenti con `--update-path`

### 🟡 Criticità 3: Nessun test
**Problema:** Nessun test unitario o di integrazione per server.py
**Impatto:** Medio — modifiche future rischiose
**Fix:** Aggiungere test con pytest

### 🟡 Criticità 4: Rate limit non visibile all'utente
**Problema:** Il server traccia internamente le chiamate API ma l'utente non ha un modo semplice per vedere quante gliene rimangono.
**Impatto:** Medio — si può sforare senza accorgersene
**Fix:** Aggiungere tool `skillsmp_status` che mostra chiamate rimanenti

### 🟡 Criticità 5: Struttura XLSX non legge skill_structure.json
**Problema:** generate_xlsx.py ha la struttura DUPLICATA nel file, invece di leggere skill_structure.json
**Impatto:** Medio — doppia manutenzione
**Fix:** generate_xlsx.py deve leggere da skill_structure.json (già parzialmente fatto)

### 🟢 Criticità 6: Nessuna GitHub Action
**Problema:** Il repo non ha CI. Nessun controllo su push.
**Impatto:** Basso ora — cresce col repo
**Fix:** Aggiungere GitHub Actions per lint + test

### 🟢 Criticità 7: SKILL.md non nel setup.ps1
**Problema:** Il setup.ps1 installa la skill ma non verifica che sia aggiornata rispetto al repo.
**Impatto:** Basso
**Fix:** Aggiungere version check o data di aggiornamento

### 🟢 Criticità 8: Nessun CHANGELOG.md
**Problema:** Non c'è storico delle modifiche.
**Impatto:** Basso
**Fix:** Creare CHANGELOG.md

### 🟢 Criticità 9: show_all_skills.py usa hardcoded DOMAINS
**Problema:** Il file ha la struttura skill hardcoded invece di leggerla da skill_structure.json
**Impatto:** Basso — script utility
**Fix:** Make it read from skill_structure.json

---

## 2. Piano Miglioramenti in 4 Microfasi

### Fase 1: Auto-scan struttura skill ⏱ ~25min
**Obiettivo:** Eliminare il disallineamento tra struttura JSON e skill reali

**Cose da fare:**
- Aggiungere script `scripts/refresh_structure.py` che:
  1. Scansiona `~/.agents/skills/`
  2. Legge ogni SKILL.md (estrai nome, descrizione dal frontmatter)
  3. Raggruppa per dominio usando il catalogo esistente come guida
  4. Salva in `data/skill_structure.json` aggiornato
- Aggiungere tool MCP `skillsmp_refresh_structure` che fa lo stesso via MCP
- Aggiornare `generate_xlsx.py` per leggere SEMPRE da skill_structure.json
- Aggiornare `show_all_skills.py` per leggere da skill_structure.json

### Fase 2: Portabilità e robustezza ⏱ ~25min
**Obiettivo:** Path relativi funzionanti, setup idempotente

**Cose da fare:**
- Aggiungere a `server.py` la risoluzione automatica del path base (usa `__file__`)
- `skill_structure.json` path risolto relativamente allo script
- `scripts/` path risolti relativamente
- Aggiornare `setup.ps1` e `setup.sh` per essere idempotenti (se ri-eseguito, aggiorna solo il path)
- Aggiungere flag `--update-path` agli script di setup

### Fase 3: Tool skillsmp_status + Test ⏱ ~30min
**Obiettivo:** Visibilità rate limit + garanzia qualità

**Cose da fare:**
- Aggiungere tool `skillsmp_status` che mostra:
  - Chiamate API oggi / limite (500)
  - Cache entries
  - SkillsMP API health
- Aggiungere `tests/test_server.py` con pytest:
  - Test rate limit tracker
  - Test cache adattiva
  - Test formattazione output
  - Test struttura skill
- Aggiungere `.github/workflows/test.yml` per GitHub Actions

### Fase 4: Documentazione e Release ⏱ ~20min
**Obiettivo:** CHANGELOG, versioning, documentazione aggiornata

**Cose da fare:**
- Creare `CHANGELOG.md` con storico v1.0.0 e v1.1.0
- Aggiornare `README.md` con:
  - Nuovo comando skillsmp_status
  - Refresh struttura
  - Badge CI
- Aggiornare `docs/skillsmp-quickref.md`
- Tag git v1.1.0
- Push finale

---

## 3. Timeline

| Fase | Cosa | Durata | Dipende da |
|------|------|--------|-----------|
| 1 | Auto-scan struttura + sync | ~25min | — |
| 2 | Portabilità (path relativi) | ~25min | — |
| 3 | skillsmp_status + Test + CI | ~30min | Fase 2 |
| 4 | CHANGELOG + Release v1.1.0 | ~20min | Tutte |
| **Totale** | | **~100min** | |

---

## 4. Risultato Atteso

| Prima | Dopo |
|-------|------|
| Struttura skill hardcoded, out of sync | Auto-scan dal filesystem, sempre sincronizzato |
| Path assoluti fragili | Path relativi, setup idempotente |
| Nessun test | Test automatici in CI (GitHub Actions) |
| Rate limit invisibile | skillsmp_status con contatore vivo |
| 3 script con struttura duplicata | Tutti leggono da skill_structure.json |
| Nessuno storico | CHANGELOG.md + git tag v1.1.0 |
