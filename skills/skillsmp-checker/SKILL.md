---
name: skillsmp-checker
description: "Verifica e confronta skill locali con SkillsMP.com. Usa i tools del source skillsmp per cercare skill aggiornate, confrontare versioni, e scoprire se esistono alternative migliori. Attivati quando l'utente chiede: 'questa skill è aggiornata?', 'c'è una skill migliore per X?', 'controlla se esiste una versione più recente', 'confronta skill', 'skillsmp', o vuole verificare la freschezza di una skill prima di implementare codice basato su di essa."
---

# SkillsMP Checker

Usa i tools del source **skillsmp** per verificare e confrontare skill con SkillsMP.com.

## Quando Usare Questa Skill

- L'utente chiede: "questa skill è aggiornata?"
- L'utente chiede: "c'è una skill migliore per X?"
- L'utente chiede: "controlla se esiste una versione più recente"
- L'utente chiede: "confronta [skill] con SkillsMP"
- L'utente vuole scoprire skill popolari su un argomento
- **PRIMA** di implementare codice basato su una skill esistente
- L'utente menziona "skillsmp"

## Prerequisiti

Il source **skillsmp** deve essere abilitato nella sessione corrente.
Tools disponibili:
- `skillsmp_search` — Ricerca keyword
- `skillsmp_ai_search` — Ricerca semantica AI
- `skillsmp_check_skill` — Verifica skill locale
- `skillsmp_compare_skills` — Confronto skill

## Procedura: Verifica Skill

1. **Identifica la skill locale** di cui l'utente vuole verificare l'aggiornamento
2. **Chiama `skillsmp_check_skill`** con il nome della skill
3. **Analizza i risultati:**
   - Confronta stelle GitHub (più stelle = più adozione/qualità)
   - Confronta data aggiornamento (più recente = più fresco)
   - Leggi la descrizione (copre gli stessi casi d'uso?)
4. **Report all'utente:** spiega se la skill locale è ancora valida o se su SkillsMP esistono alternative migliori
5. **Se ci sono alternative migliori**, mostra nome, autore, stelle e link

## Procedura: Ricerca Esplorativa

1. **Chiedi cosa vuole fare l'utente** (se non è specifico)
2. Usa `skillsmp_ai_search` per descrizioni vaghe ("voglio fare web scraping")
3. Usa `skillsmp_search` per argomenti specifici ("stripe payment")
4. **Ordina per stelle** per trovare le skill più popolari
5. **Mostra risultati** con nome, autore, stelle, descrizione, link

## Esempi di Query Efficaci

| Cosa cerchi | Query | Filtro |
|------------|-------|--------|
| Stripe payments | `skillsmp_search(q="stripe payment", sortBy="stars")` | category="payment" |
| React components | `skillsmp_search(q="react component", sortBy="stars")` | category="frontend" |
| ML pipeline | `skillsmp_search(q="machine learning pipeline", sortBy="stars")` | category="llm-ai" |
| CI/CD automation | `skillsmp_search(q="ci cd", sortBy="stars")` | category="cicd" |
| Descrizione vaga | `skillsmp_ai_search(q="How to build a dashboard with charts")` | — |

## Cosa NON Fare

- ❌ Non sostituire automaticamente le skill locali con quelle di SkillsMP
- ❌ Non implementare codice seguendo ciecamente una skill di SkillsMP senza verificare
- ❌ Non ignorare il rate limit (500/giorno)
- ✅ Usa SkillsMP come **fonte di verifica e scoperta**, non come autorità assoluta

---

*Parte del progetto [github.com/matrixNeo76/skillsmp-mcp](https://github.com/matrixNeo76/skillsmp-mcp)*
