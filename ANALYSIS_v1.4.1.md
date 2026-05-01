# Codebase Analysis v1.4.1 — Report + Piano

> Data: 2026-05-02

---

## Parte 1: Criticita Identificate (8)

### 🔴 Criticita 1: Versione hardcoded in server.py
**File:** `server.py:63`
**Problema:** `SERVER_VERSION = "1.2.0"` hardcoded, ma VERSION file dice 1.4.0.
La versione letta dallo status tool e' **sbagliata** (mostra 1.2.0 invece di 1.4.0).
**Impatto:** Alto — status tool mostra versione errata, confusionaria
**Fix:** Leggere da VERSION file, non hardcodare

### 🔴 Criticita 2: Documenti non aggiornati a v1.4.x
**File:** `README.md`, `AGENTS.md`, `CHANGELOG.md`
**Problema:**
- README.md: badge versione 1.3.0
- AGENTS.md: versione 1.3.0
- CHANGELOG.md: manca v1.4.0 e v1.4.1
**Impatto:** Medio — documentazione disallineata
**Fix:** Aggiornare badge, versioni, aggiungere changelog

### 🟡 Criticita 3: 5 funzioni >70 righe (server.py)
**File:** `server.py`
**Problema:**
- `skillsmp_check_outdated`: 160 righe
- `skillsmp_skill_diff`: 122 righe
- `skillsmp_scan_domain`: 102 righe
- `skillsmp_discover`: 100 righe
- `skillsmp_install_skill`: 99 righe
Funzioni troppo lunghe = difficile manutenere.
**Impatto:** Medio — complessita' crescente
**Fix:** Estrarre helper dalle funzioni piu' lunghe

### 🟡 Criticita 4: README non aggiornato con tutti gli 11 tools
**File:** `README.md`
**Problema:** README menziona 8 tools, mancano gli ultimi 3
(check_outdated, discover, install_skill).
**Impatto:** Medio — utenti non sanno cosa esiste
**Fix:** Aggiornare tool table nel README

### 🟢 Criticita 5: server.py ancora >1.200 righe
**File:** `server.py` (1.296 righe)
**Problema:** 11 tools in un unico file. utils.py creato ma non usato.
**Impatto:** Basso — manutenibile ma scomodo
**Fix:** Progressivo refactoring: spostare 1-2 tool alla volta in utils.py

### 🟢 Criticita 6: Nessuna validazione input per github_url in install_skill
**File:** `server.py:skillsmp_install_skill`
**Problema:** L'URL GitHub non viene validato prima dello scaricamento.
Si puo' passare qualsiasi URL.
**Impatto:** Basso — uso locale, ma...
**Fix:** Validare che l'URL sia un raw GitHub URL

### 🟢 Criticita 7: Nessun timeout configurabile per singola chiamata
**File:** `server.py`
**Problema:** `REQUEST_TIMEOUT = 15` e' l'unico timeout per TUTTE le chiamate.
SkillsMP a volte e' lento sull'AI search.
**Impatto:** Basso — timeout generico funziona
**Fix:** Timeout differenziato per AI search (piu' lungo)

### 🟢 Criticita 8: Cache persistente non espone count via status
**File:** `server.py:skillsmp_status`
**Problema:** Lo status mostra cache in-memory entries ma non la persistent cache.
**Impatto:** Basso — manca visibilita'
**Fix:** Aggiungere persistent_cache count allo status

---

## Parte 2: Piano Mitigazione in 4 Microfasi

### Fase 1: Fix Critico — Versioni ⏱ ~10min
| # | Criticita | Fix |
|---|-----------|-----|
| 1 | Versione hardcoded | `server.py:63`: leggere da VERSION file invece di hardcodare |
| 2 | Documenti outdated | README badge → 1.4.1, CHANGELOG → v1.4.0 + v1.4.1, AGENTS → 1.4.1 |

**Output:** Versione corretta nello status, documenti allineati

### Fase 2: README Completo ⏱ ~10min
| # | Criticita | Fix |
|---|-----------|-----|
| 3 | README 8 tools | Aggiungere check_outdated, discover, install_skill alla tool table |
| 2 | Badge versione | Passare da 1.3.0 a 1.4.1 |

**Output:** README con tutti gli 11 tools documentati

### Fase 3: Refactoring Funzioni Lunghe ⏱ ~20min
| # | Criticita | Fix |
|---|-----------|-----|
| 4 | 5 funzioni >70 righe | Estrarre helper: _outdated_line(), _discover_line(), _install_verify_url() |
| 5 | server.py 1.296 righe | Ridurre a ~1.100 con estrazione helper |

**Output:** Funzioni piu' corte, codice piu' leggibile

### Fase 4: Miglioramenti Minori ⏱ ~10min
| # | Criticita | Fix |
|---|-----------|-----|
| 6 | URL non validato | Validazione github_url in install_skill |
| 7 | Timeout unico | Timeout 30s per AI search |
| 8 | Cache count in status | Aggiungere persistent_cache count a skillsmp_status |

**Output:** Piu' robustezza, piu' visibilita'

---

## Timeline

| Fase | Cosa | Durata | Test |
|------|------|--------|------|
| 1 | Fix versioni + docs | ~10min | 27 → 27 |
| 2 | README completo 11 tools | ~10min | 27 → 27 |
| 3 | Refactoring funzioni lunghe | ~20min | 27 → 30 |
| 4 | Miglioramenti minori | ~10min | 30 → 30 |
| **Totale** | | **~50min** | **30 test** |
