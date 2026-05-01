# Politiche di Sicurezza

## API Key

SkillsMP MCP Server richiede una API key per funzionare.
Non condividere mai la tua API key.

### Buone Pratiche
- La API key va impostata come **variabile d'ambiente** (`SKILLSMP_API_KEY`)
- Mai hardcodata nel codice
- Mai committata nel repository (`.gitignore` blocca `.env`)
- Setup.ps1 e setup.sh la chiedono interattivamente (non la salvano in chiaro nei log)

### Se la API Key viene Compromessa
1. Rigenerarla su https://skillsmp.com
2. Aggiornare `~/.mcp.json` con la nuova chiave

## Rate Limiting

Il server SkillsMP ha un rate limit di 500 richieste/giorno.
Il server MCP traccia internamente le chiamate per evitare di superare il limite.

- Usa `skillsmp_status` per vedere le chiamate rimanenti
- La cache adattiva riduce le chiamate duplicate
- Se il limite viene raggiunto, i tool restituiscono un errore HTTP 429

## Dipendenze

Le dipendenze Python sono gestite via `pyproject.toml`.
Mantenere le dipendenze aggiornate per evitare vulnerabilita' note.

```bash
pip install --upgrade fastmcp httpx openpyxl
```

## Segnalare Vulnerabilità

Per vulnerabilità critiche, aprire una issue su GitHub con label `security`.
Non divulgare vulnerabilità critiche pubblicamente prima della risoluzione.

## Permessi

- Il MCP server non richiede permessi di amministratore
- Opera solo in lettura su SkillsMP.com
- Scrive solo in `data/skill_structure.json` (refresh struttura)
- Le API key sono gestite via variabili d'ambiente
