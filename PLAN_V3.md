# SkillsMP MCP — Analisi e Piano v1.2.0

> Data: 2026-05-01
> Stato attuale: 7 tools, 581 skill, 14 test, 99% categorizzazione

---

## 1. Criticità Identificate (6)

### 🟡 Criticità 1: Struttura non auto-aggiornata allo start
**Problema:** `skill_structure.json` si aggiorna solo con `skillsmp_refresh_structure`. 
Se si installano nuove skill tra una sessione e l'altra, la struttura resta vecchia.
**Impatto:** Medio — scan_domain usa dati obsoleti
**Fix:** Auto-refresh struttura all'avvio del MCP server

### 🟡 Criticità 2: Nessun confronto contenuto local vs SkillsMP
**Problema:** Possiamo vedere stelle e date SkillsMP, ma non se il contenuto 
della SKILL.md locale è diverso da quello su SkillsMP.
**Impatto:** Medio — non sappiamo se la skill e' cambiata sostanzialmente
**Fix:** Nuovo tool `skillsmp_skill_diff` che confronta descrizioni

### 🟡 Criticità 3: Nessun export CSV
**Problema:** L'inventario e' solo in XLSX (richiede Excel/LibreOffice).
**Impatto:** Medio — meno accessibile su sistemi senza Office
**Fix:** Aggiungere `--csv` al generate_xlsx.py o nuovo script

### 🟢 Criticità 4: Versione hardcoded in server.py
**Problema:** `"server_version": "2.0.0"` e' hardcoded nello status.
Da aggiornare manualmente ad ogni rilascio.
**Impatto:** Basso — dimenticanza possibile
**Fix:** Leggere versione da pyproject.toml o file dedicato

### 🟢 Criticità 5: Nessun pre-commit hook
**Problema:** refresh_structure.py va eseguito manualmente prima dei commit.
**Impatto:** Basso — la struttura puo' uscire di sincrono
**Fix:** Aggiungere script pre-commit opzionale

### 🟢 Criticità 6: SKILL.md non linka al repo GitHub
**Problema:** La SKILL.md non contiene reference al repo skillsmp-mcp su GitHub.
**Impatto:** Basso
**Fix:** Aggiornare SKILL.md con link al repo e docs

---

## 2. Piano in 4 Microfasi

### Fase 1: Auto-refresh + Versione ⏱ ~20min
**Obiettivo:** Struttura sempre sincronizzata, versione gestita

**Cose da fare:**
- `server.py`: all'avvio, esegue refresh_structure.py automaticamente
- `server.py`: leggere versione da file dedicato `VERSION` (semplice txt)
- `pyproject.toml`: version sync
- Test: verifica che auto-refresh funzioni

### Fase 2: skillsmp_skill_diff ⏱ ~25min
**Obiettivo:** Confronto contenuto tra skill locale e SkillsMP

**Cose da fare:**
- Nuovo tool `skillsmp_skill_diff(skill_name)`:
  1. Legge descrizione dalla SKILL.md locale
  2. Cerca su SkillsMP la skill corrispondente
  3. Confronta le descrizioni (distanza di similarità)
  4. Report: "IDENTICA", "SIMILE", "DIVERSA"
- Output: differenze evidenziate

### Fase 3: Export CSV ⏱ ~15min
**Obiettivo:** Inventario esportabile anche senza Excel

**Cose da fare:**
- Aggiungere flag `--csv` a `scripts/generate_xlsx.py`
- CSV con stesse colonne dell'XLSX
- Delimitatore standard (virgola) per compatibilità universale

### Fase 4: Pre-commit hook + SKILL.md update ⏱ ~15min
**Obiettivo:** Automazione e documentazione

**Cose da fare:**
- Script `scripts/install-hooks.sh` e `scripts/install-hooks.ps1`
- Pre-commit hook che esegue refresh_structure.py prima del commit
- Aggiornare `skills/skillsmp-checker/SKILL.md` con link al repo GitHub
- Aggiornare README con nuove funzionalità

---

## 3. Timeline

| Fase | Cosa | Durata |
|------|------|--------|
| 1 | Auto-refresh + versione gestita | ~20min |
| 2 | skillsmp_skill_diff | ~25min |
| 3 | Export CSV | ~15min |
| 4 | Pre-commit hook + SKILL.md update | ~15min |
| **Totale** | | **~75min** |

## 4. Risultato Atteso (v1.2.0)

| Ora | Dopo |
|-----|------|
| Struttura aggiornata manualmente | Auto-refresh all'avvio |
| Versione hardcoded "2.0.0" | Versione da VERSION file |
| Nessun confronto contenuto | `skillsmp_skill_diff` mostra differenze |
| Solo XLSX | XLSX + CSV |
| Struttura può uscire di sincrono | Pre-commit hook la aggiorna |
| SKILL.md senza contesto | SKILL.md linka al repo GitHub |
