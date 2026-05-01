# SkillsMP MCP — Analisi e Piano v1.4.0

> Data: 2026-05-01
> Baseline: 9 tools, 582 skill, 19 test, v1.3.0

---

## 1. Criticita Identificate (7)

### 🔴 Criticita 1: Cache persa ad ogni riavvio del server
**Problema:** La cache e' in-memory. Quando il server MCP si riavvia (cambio sessione,
errore, etc.), tutte le risposte SkillsMP vengono perse e rifatte da capo.
**Impatto:** Alto — spreco di API call (500/giorno) per dati gia' recuperati
**Fix:** Cache persistente su file JSON in `data/` (con TTL)

### 🔴 Criticita 2: Nessuna scoperta di skill nuove
**Problema:** I tool verificano SOLO skill che gia' abbiamo. Non possiamo
scoprire "cosa c'e' di bello su SkillsMP che non ho".
**Impatto:** Medio — ci perdiamo skill potenzialmente utili
**Fix:** Nuovo tool `skillsmp_discover(category, min_stars)` che cerca su SkillsMP
skill che NON sono nella nostra struttura locale, filtrando per categoria

### 🟡 Criticita 3: Nessuna installazione skill dal MCP
**Problema:** Per installare una skill scoperta da SkillsMP, bisogna uscire dal
flusso MCP, cercare il repo GitHub, copiare manualmente.
**Impatto:** Medio — flusso interrotto
**Fix:** Nuovo tool `skillsmp_install_skill(skill_name, github_url)` che scarica
la SKILL.md e la installa in `.agents/skills/`

### 🟡 Criticita 4: Categorie SkillsMP non esplorabili
**Problema:** `skillsmp_search` accetta `category` ma non c'e' modo di vedere
l'elenco delle categorie disponibili.
**Impatto:** Basso-Medio — scopribilita' ridotta
**Fix:** Aggiungere endpoint o tabella di categorie SkillsMP

### 🟢 Criticita 5: check_outdated non esportabile
**Problema:** Il report outdated esce solo in console. Non si puo' salvare
come CSV/XLSX per analisi offline.
**Impatto:** Basso — workflow manuale
**Fix:** Aggiungere flag `--save` a `skillsmp_check_outdated` che scrive CSV

### 🟢 Criticita 6: Test non coprono check_outdated e scan_domain
**Problema:** 19 test coprono 7/9 tools. Mancano test per `check_outdated` e
`scan_domain` (i piu' complessi).
**Impatto:** Basso — ma regressioni possibili
**Fix:** Aggiungere test per i 2 tools mancanti -> 21+ test

### 🟢 Criticita 7: Aggiornamento XLSX bulk consuma tutte le API
**Problema:** `generate_xlsx.py --with-skillsmp` fa 580+ chiamate API = l'intero
budget giornaliero in un colpo.
**Impatto:** Basso — ma blocca altri strumenti per 24h
**Fix:** Aggiungere `--batch-size` per limitare chiamate, avviso prima di iniziare

---

## 2. Piano in 4 Microfasi

### Fase 1: Cache persistente su file ⏱ ~20min
**Obiettivo:** Cache che sopravvive ai riavvii del server

**Cose da fare:**
- `server.py`: aggiungere `PersistentCache` classe che salva in
  `data/cache_skillsmp.json` (JSON con {key: {data, expires_at}})
- Cache ricaricata all'avvio, entries scadute ignorate
- TTL: default 300s, stabile 600s (come cache in-memory)
- La cache in-memory rimane come fallback veloce

### Fase 2: skillsmp_discover + categorie ⏱ ~30min
**Obiettivo:** Scoprire skill nuove da SkillsMP

**Cose da fare:**
- Nuovo tool `skillsmp_discover(category, min_stars)`:
  1. Cerca su SkillsMP per categoria
  2. Confronta con skill locali
  3. Filtra quelle che NON abbiamo
  4. Ordina per stelle
- Tabella categorie SkillsMP con slug: `payment`, `frontend`, `backend`,
  `llm-ai`, `cicd`, `cloud`, `security`, `testing`, `database`, `devops`, etc.

### Fase 3: skillsmp_install_skill + test aggiuntivi ⏱ ~25min
**Obiettivo:** Installare skill scoperte + copertura test 100% tools

**Cose da fare:**
- Nuovo tool `skillsmp_install_skill(skill_name, github_url)`:
  1. Scarica SKILL.md da GitHub (raw URL)
  2. Crea directory in `.agents/skills/<name>/`
  3. Salva SKILL.md
  4. Aggiorna struttura skill
- Aggiungere test per `check_outdated` e `scan_domain` -> 23+ test

### Fase 4: Export outdated CSV + avviso batch XLSX ⏱ ~15min
**Obiettivo:** Dati esportabili, protezione rate limit

**Cose da fare:**
- `server.py`: `skillsmp_check_outdated` aggiungere parametro `save_csv`
- `scripts/generate_xlsx.py`: aggiungere `--batch-size N` per limitare
  chiamate API, e avviso se >200 chiamate stimate
- Controllo preventivo: se chiamate stimate + calls_today > 450, blocca

---

## 3. Timeline

| Fase | Cosa | Durata |
|------|------|--------|
| 1 | Cache persistente su file | ~20min |
| 2 | skillsmp_discover + categorie | ~30min |
| 3 | skillsmp_install_skill + test aggiuntivi | ~25min |
| 4 | Export CSV + protezione batch | ~15min |
| **Totale** | | **~90min** |

## 4. Risultato Atteso (v1.4.0)

| Ora | Dopo |
|-----|------|
| Cache persa al riavvio | Cache persistente su file JSON |
| Solo verifica skill esistenti | `skillsmp_discover` trova skill nuove |
| Nessuna installazione da MCP | `skillsmp_install_skill` installa da GitHub |
| Categorie non esplorabili | Tabella categorie + filtro discover |
| Report solo in console | `check_outdated` esportabile in CSV |
| 19 test | 23+ test (tutti i tools coperti) |
| XLSX bulk brucia API | `--batch-size` + avviso preventivo |
