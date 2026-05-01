# SkillsMP MCP — Analisi Approfondita v1.3

> Data: 2026-05-01
> Baseline: 8 tools, 581 skill, 14 test, 23 files

---

## 1. Criticita Identificate (8)

### 🔴 Criticita 1: Test coprono solo utility, non i tool MCP
**Problema:** I 14 test coprono RateLimitTracker, cache, formattazione e struttura,
ma **nessun test** per i tool MCP veri e propri (skill_diff, status, scan_domain, etc.).
Un refactoring di `server.py` puo' rompere tools senza che i test se ne accorgano.
**Impatto:** Alto — falsa sicurezza, regressioni silenziose
**Fix:** Aggiungere test di integrazione per ogni tool MCP

### 🔴 Criticita 2: Struttura JSON senza metadati di refresh
**Problema:** `skill_structure.json` non contiene timestamp di ultimo aggiornamento.
Non si sa se la struttura e' fresca o vecchia di giorni.
**Impatto:** Medio — confusione su sincronizzazione
**Fix:** Aggiungere campo `_meta` con timestamp, conteggi, versione

### 🟡 Criticita 3: Nessun check bulk "outdated"
**Problema:** Per sapere TUTTE le skill obsolete, bisogna chiamare `scan_domain` per
ognuno dei 17 domini (17 chiamate batch). Non esiste un comando unico.
**Impatto:** Medio — workflow lento per overview completa
**Fix:** Nuovo tool `skillsmp_check_outdated()` che scansiona tutto e produce
report prioritizzato (skill con stelle SkillsMP molto maggiori delle locali)

### 🟡 Criticita 4: Auto-refresh startup potenzialmente lento
**Problema:** Ogni avvio del server esegue `refresh_structure.py` (subprocess).
Su macchine con 500+ skill, aggiunge 2-3 secondi allo start.
**Impatto:** Basso-Medio — percepibile su start frequenti
**Fix:** Auto-refresh solo se struttura ha piu' di 1 ora, o flag `--no-refresh`

### 🟡 Criticita 5: Nessun file di configurazione
**Problema:** Cache TTL, path, comportamenti sono hardcodati in `server.py`.
Per modificarli serve editing del codice.
**Impatto:** Basso — ma cresce con la complessita'
**Fix:** Aggiungere supporto per `skillsmp-config.json` (opzionale, con default)

### 🟢 Criticita 6: Nessun .env support
**Problema:** `SKILLSMP_API_KEY` va impostata come env o in `.mcp.json`.
Nessun supporto per file `.env` standard.
**Impatto:** Basso — comodo ma non essenziale
**Fix:** Caricare `.env` se presente (con python-dotdown opzionale)

### 🟢 Criticita 7: show_all_skills.py minimalista
**Problema:** Lo script ha solo 80 righe, output poco strutturato.
**Impatto:** Basso — script utility minore
**Fix:** Aggiungere opzioni: `--domain`, `--outdated`, `--format json`

### 🟢 Criticita 8: Nessuna integrazione .mcp.json automatica
**Problema:** Il setup copia, ma non c'e' un tool MCP per auto-configurare
il `.mcp.json` su una nuova macchina.
**Impatto:** Basso — setup manuale funziona
**Fix:** Aggiungere tool `skillsmp_setup_wizard` interattivo

---

## 2. Piano in 4 Microfasi

### Fase 1: Metadati struttura + Config file ⏱ ~20min
**Obiettivo:** Struttura tracciabile, server configurabile

**Cose da fare:**
- `refresh_structure.py`: aggiungere `_meta` a skill_structure.json:
  ```json
  {
    "_meta": {
      "version": "1.3.0",
      "last_refresh": "2026-05-01T20:00:00",
      "total_skills": 581,
      "domains": 17
    },
    "domains": [...]
  }
  ```
- `server.py`: caricare `skillsmp-config.json` opzionale per sovrascrivere default
- Config supportato: `cache_ttl`, `stable_ttl`, `auto_refresh`, `max_retries`
- Test: verifica che _meta sia presente e corretto

### Fase 2: skillsmp_check_outdated ⏱ ~25min
**Obiettivo:** Report unico di tutte le skill obsolete

**Cose da fare:**
- Nuovo tool `skillsmp_check_outdated()`:
  1. Scansiona TUTTE le 581 skill su SkillsMP
  2. Per ognuna, confronta: stelle SkillsMP, data aggiornamento
  3. Calcola "outdated score" = stelle_skillsmp - stima_locali
  4. Restituisce top 20 piu' obsolete
  5. Opzione `--domain` per limitare a un dominio
- Output: tabella priorizzata "NOME | ⭐ SkillsMP | DATA | PRIORITA'"

### Fase 3: Test integrazione per tools MCP ⏱ ~20min
**Obiettivo:** Ogni tool MCP ha almeno un test

**Cose da fare:**
- Aggiungere test per:
  - `skillsmp_status`: verifica struttura output JSON
  - `skillsmp_skill_diff`: verifica con skill esistente e inesistente
  - `skillsmp_refresh_structure`: verifica che script esista e parta
  - `skillsmp_scan_domain`: verifica gestione dominio inesistente
- Mockare le chiamate API SkillsMP per test offline
- Totale test: da 14 a ~20

### Fase 4: Ottimizzazioni + show_all_skills.py ⏱ ~15min
**Obiettivo:** Velocita' startup, script migliore

**Cose da fare:**
- `server.py`: auto-refresh solo se struttura ha piu' di 1 ora
- `server.py`: flag `--no-refresh` per bypassare auto-refresh
- `scripts/show_all_skills.py`: aggiungere opzioni:
  - `--domain 3` (filtra per dominio)
  - `--outdated` (solo skill candidate a update)
  - `--format json` (output machine-readable)
  - `--limit N` (massimo risultati)

---

## 3. Timeline

| Fase | Cosa | Durata |
|------|------|--------|
| 1 | Metadati struttura + Config file | ~20min |
| 2 | skillsmp_check_outdated | ~25min |
| 3 | Test integrazione tools MCP | ~20min |
| 4 | Ottimizzazioni + show_all upgrade | ~15min |
| **Totale** | | **~80min** |

## 4. Risultato Atteso (v1.3.0)

| Ora | Dopo |
|-----|------|
| Struttura senza metadata | `_meta` con timestamp, versione, conteggi |
| Parametri hardcodati | `skillsmp-config.json` opzionale |
| Nessun check bulk outdated | `skillsmp_check_outdated` report prioritizzato |
| 14 test solo utility | ~20 test inclusi integration per tools MCP |
| Auto-refresh sempre | Solo se struttura >1 ora, o `--no-refresh` |
| show_all_skills 80 righe | Script potenziato con filtri e formati |
