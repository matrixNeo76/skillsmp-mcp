# Piano Mitigazione Criticita — v1.4.1

> Baseline: v1.4.0 (11 tools, 23 test, 9 issues)
> Obiettivo: Risolvere tutte e 9 le criticita in 4 microfasi

---

## Fase 1: Pulizia Codice ⏱ ~10min

**Criticita:** 1, 5, 7

| # | Criticita | Fix |
|---|-----------|-----|
| 1 | `import re` dentro funzione (L824) | Spostare in cima a server.py |
| 5 | `typing` importato ma poco usato | Sostituire con `Optional` inline o rimuovere |
| 7 | `_load_skill_structure` usato da 1 solo tool | Refactor: estrarlo e usarlo in tutti i tool che caricano struttura |

**Cose da fare:**
- `server.py`: spostare `import re` in cima (linea ~10)
- `server.py`: rimuovere `from typing import Optional`, usare type hints Python 3.11+ (`str | None`)
- `server.py`: consolidare tutti i caricamenti struttura in `_load_skill_structure()`
- `server.py`: `_load_skill_structure()` diventa l'unico modo per accedere alla struttura

## Fase 2: Setup + Documentazione ⏱ ~10min

**Criticita:** 2, 6, 8

| # | Criticita | Fix |
|---|-----------|-----|
| 2 | setup.sh non eseguibile | `git add --chmod=+x setup.sh` |
| 6 | SKILL.md non allineata con 11 tools | Aggiornare tool table completa |
| 8 | Nessun supporto `.env` | Aggiungere `python-dotenv` opzionale in pyproject.toml |

**Cose da fare:**
- `git add --chmod=+x setup.sh`
- `skills/skillsmp-checker/SKILL.md`: aggiungere tabella con tutti e 11 i tools
- `pyproject.toml`: aggiungere `python-dotenv` come dipendenza opzionale
- `server.py`: all'avvio, caricare `.env` se presente

## Fase 3: +4 Test per copertura 100% ⏱ ~15min

**Criticita:** 3

| Tool mancante | Test da creare |
|--------------|----------------|
| `skillsmp_search` | Verifica output JSON + gestione query vuota |
| `skillsmp_check_outdated` | Verifica struttura output JSON |
| `skillsmp_discover` | Verifica categories + categoria invalida |
| `skillsmp_scan_domain` | Verifica dominio inesistente |

**Cose da fare:**
- `tests/test_server.py`: aggiungere 4 test
- Verificare che tutti passino (23 → 27)

## Fase 4: Refactoring Strutturale ⏱ ~15min

**Criticita:** 4, 9

| # | Criticita | Fix |
|---|-----------|-----|
| 4 | Cache persistente quasi vuota | Forzare popolamento con refresh season |
| 9 | server.py >1.200 righe | Estrarre `utils.py` con utilita' riutilizzabili |

**Cose da fare:**
- Creare `server/utils.py` con:
  - `RateLimitTracker`
  - `_get_ttl()`, `_api_call()`, `_cached_or_fetch()`
  - `PersistentCache` (load/save)
  - `_format_date()`, `_format_search_results()`
  - `SKILLSMP_CATEGORIES`
- `server.py`: importare da `server.utils` invece di definire tutto inline
- Righe server.py: da ~1.291 a ~800

---

## Timeline

| Fase | Cosa | Durata | Test |
|------|------|--------|------|
| 1 | Pulizia codice (import, dead code) | ~10min | 23 → 23 |
| 2 | Setup + Documentazione | ~10min | 23 → 23 |
| 3 | +4 Test | ~15min | 23 → **27** |
| 4 | Refactoring utils.py | ~15min | 27 → 27 |
| **Totale** | | **~50min** | **27 test** |

## Output Atteso (v1.4.1)

| Criticita | Prima | Dopo |
|-----------|-------|------|
| 1. import re in funzione | Inefficiente | In cima al file |
| 2. setup.sh non eseguibile | `bash setup.sh` | `./setup.sh` |
| 3. 4 tool senza test | 23 test | **27 test** |
| 4. Cache vuota | 1 entry | Popolata |
| 5. typing inutilizzato | Import spazzatura | Pulito |
| 6. SKILL.md outdated | 8 tools menzionati | **11 tools** |
| 7. _load_skill_structure sottoutilizzato | Usato da 1 tool | Usato da tutti |
| 8. Nessun .env | Solo env manuale | `python-dotenv` opzionale |
| 9. server.py >1.200 righe | 1.291 righe | **~800 righe** |
