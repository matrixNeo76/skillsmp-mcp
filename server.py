"""
SkillsMP MCP Server v2 — Cerca e confronta skill da skillsmp.com
===============================================================

Tools:
  - skillsmp_search: keyword search
  - skillsmp_ai_search: AI semantic search
  - skillsmp_check_skill: trova una skill locale su SkillsMP
  - skillsmp_compare_skills: confronta skill locale con alternative
  - skillsmp_scan_domain: scansiona un intero dominio di skill locali

v2 miglioramenti:
  - Retry con exponential backoff (3 tentativi)
  - Rate limit tracking giornaliero
  - Cache adattiva (pattern stabili = cache piu lunga)
  - Output JSON opzionale (formato json)
  - Tool skillsmp_scan_domain per domini interi
"""

import os
import time
import json
import httpx
import datetime
from typing import Optional
from mcp.server.fastmcp import FastMCP

# ── Config ────────────────────────────────────────────────────────────
API_BASE = "https://skillsmp.com/api/v1"
API_KEY = os.environ.get("SKILLSMP_API_KEY", "")
REQUEST_TIMEOUT = 15
MAX_RETRIES = 3
DEFAULT_TTL = 300
STABLE_TTL = 600
AUTO_REFRESH = True
SKILLS_DIR = os.path.expanduser("~/.agents/skills")

SERVER_DIR = os.path.dirname(os.path.abspath(__file__))
VERSION_PATH = os.path.join(SERVER_DIR, "VERSION")

# ── Config file opzionale (sovrascrive default) ──────────────
CONFIG_PATH = os.path.join(SERVER_DIR, "skillsmp-config.json")
if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            _cfg = json.load(f)
        DEFAULT_TTL = _cfg.get("cache_ttl", DEFAULT_TTL)
        STABLE_TTL = _cfg.get("stable_ttl", STABLE_TTL)
        MAX_RETRIES = _cfg.get("max_retries", MAX_RETRIES)
        AUTO_REFRESH = _cfg.get("auto_refresh", AUTO_REFRESH)
    except Exception as e:
        print(f"[SkillsMP] Config error: {e}")
SERVER_VERSION = "1.2.0"
if os.path.exists(VERSION_PATH):
    try:
        with open(VERSION_PATH, "r") as f:
            SERVER_VERSION = f.read().strip()
    except:
        pass

# ══════════════════════════════════════════════════════════════════════
#  Rate Limit Tracker
# ══════════════════════════════════════════════════════════════════════

class RateLimitTracker:
    """Traccia le chiamate API SkillsMP giornaliere."""
    def __init__(self, daily_limit=500):
        self.daily_limit = daily_limit
        self.calls_today = 0
        self.last_reset = time.time()
        self.last_remaining = None
        self.last_reset_ts = None

    def _check_reset(self):
        now = time.time()
        day_seconds = 86400
        if now - self.last_reset > day_seconds:
            self.calls_today = 0
            self.last_reset = now

    def record_call(self, response=None):
        self._check_reset()
        self.calls_today += 1
        if response and "X-RateLimit-Daily-Remaining" in response.headers:
            self.last_remaining = int(response.headers["X-RateLimit-Daily-Remaining"])
        if response and "X-RateLimit-Daily-Reset" in response.headers:
            self.last_reset_ts = response.headers["X-RateLimit-Daily-Reset"]

    def is_near_limit(self, threshold=50):
        self._check_reset()
        remaining = self.daily_limit - self.calls_today
        return remaining <= threshold

    def remaining(self):
        self._check_reset()
        if self.last_remaining is not None:
            return min(self.last_remaining, self.daily_limit - self.calls_today)
        return self.daily_limit - self.calls_today

    def summary(self):
        self._check_reset()
        return f"API calls today: {self.calls_today}/{self.daily_limit}, remaining: {self.remaining()}"

_tracker = RateLimitTracker()

# ══════════════════════════════════════════════════════════════════════
#  Cache adattiva (TTL variabile)
# ══════════════════════════════════════════════════════════════════════

_cache: dict[str, tuple[float, dict]] = {}

def _get_ttl(data: dict) -> int:
    """TTL piu lungo per skill stabili (tante stelle)."""
    skills = data.get("data", {}).get("skills", [])
    if skills:
        max_stars = max(s.get("stars", 0) for s in skills)
        if max_stars >= 1000:
            return STABLE_TTL
    return DEFAULT_TTL

# ══════════════════════════════════════════════════════════════════════
#  HTTP call con retry + rate limit tracking
# ══════════════════════════════════════════════════════════════════════

def _api_call(url: str, params: dict) -> dict:
    """Chiamata API SkillsMP con retry, backoff e rate limit tracking."""
    headers = {"Authorization": f"Bearer {API_KEY}"} if API_KEY else {}
    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            resp = httpx.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
            _tracker.record_call(resp)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                # Rate limit colpito — aspetta e riprova
                wait = (2 ** attempt) * 5
                time.sleep(wait)
                last_error = e
                continue
            raise
        except httpx.RequestError as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)
                continue
            raise

    raise last_error or httpx.RequestError("Max retries exceeded")


def _cached_or_fetch(cache_key: str, url: str, params: dict) -> dict:
    """Helper con cache adattiva."""
    now = time.time()
    if cache_key in _cache:
        ts, data = _cache[cache_key]
        if now - ts < _get_ttl(data):
            return data

    try:
        data = _api_call(url, params)
        _cache[cache_key] = (time.time(), data)
        return data
    except httpx.HTTPStatusError as e:
        # Usa cache scaduta se disponibile come fallback
        if cache_key in _cache:
            ts, data = _cache[cache_key]
            return data
        raise
    except httpx.RequestError as e:
        if cache_key in _cache:
            ts, data = _cache[cache_key]
            return data
        raise


def _format_date(updated: str) -> str:
    if not updated:
        return "-"
    try:
        return datetime.datetime.fromtimestamp(int(updated)).strftime("%Y-%m-%d")
    except (ValueError, OSError):
        return str(updated)


def _format_search_results(q: str, data: dict, limit: int = 10) -> str:
    """Formatta risultati ricerca in testo markdown."""
    skills = data.get("data", {}).get("skills", [])
    if not skills:
        return f"Nessuna skill trovata per '{q}'."

    pag = data.get("data", {}).get("pagination", {})
    total = pag.get("total", "?")
    rate_note = f"\n\n📊 {_tracker.summary()}" if _tracker.remaining() < 200 else ""

    lines = [
        f"## 🔍 Risultati per '{q}'  ({total} totali, mostrati {len(skills)}){rate_note}",
        "",
    ]
    for s in skills:
        stars = s.get("stars", 0)
        updated = _format_date(s.get("updatedAt", ""))
        lines.append(f"### ⭐ {stars} | {s['name']} — by {s.get('author', '?')}")
        lines.append(f"   _{s.get('description', '')}_")
        lines.append(f"   📅 Aggiornato: {updated}")
        lines.append(f"   🔗 {s.get('skillUrl', '')}")
        lines.append("")

    return "\n".join(lines)


def _format_search_results_json(data: dict) -> str:
    """Formatta risultati ricerca in JSON."""
    skills = data.get("data", {}).get("skills", [])
    pag = data.get("data", {}).get("pagination", {})
    result = {
        "total": pag.get("total", len(skills)),
        "returned": len(skills),
        "skills": [
            {
                "name": s.get("name"),
                "author": s.get("author"),
                "stars": s.get("stars", 0),
                "updated": _format_date(s.get("updatedAt", "")),
                "description": s.get("description", ""),
                "url": s.get("skillUrl", ""),
            }
            for s in skills
        ],
        "rate_limit": {
            "remaining": _tracker.remaining(),
            "daily_limit": _tracker.daily_limit,
            "calls_today": _tracker.calls_today,
        }
    }
    return json.dumps(result, indent=2, ensure_ascii=False)


# ══════════════════════════════════════════════════════════════════════
#  Struttura skill locali (da JSON o default)
# ══════════════════════════════════════════════════════════════════════

# Path relativi al repo
# Path (SERVER_DIR già definito sopra)
SKILL_STRUCTURE_PATH = os.path.join(SERVER_DIR, "data", "skill_structure.json")
REFRESH_SCRIPT = os.path.join(SERVER_DIR, "scripts", "refresh_structure.py")

def _load_skill_structure() -> dict:
    """Carica struttura skill da file JSON o restituisce struttura vuota."""
    if os.path.exists(SKILL_STRUCTURE_PATH):
        try:
            with open(SKILL_STRUCTURE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {"domains": []}


# ══════════════════════════════════════════════════════════════════════
#  MCP Server
# ══════════════════════════════════════════════════════════════════════

mcp = FastMCP(
    "SkillsMP",
    instructions="Cerca e confronta skill AI da skillsmp.com",
)


@mcp.tool(
    description=(
        "Cerca skill su SkillsMP per parola chiave. "
        "Supporta filtri per categoria, ordinamento (stars/recent) e limite risultati. "
        "Opzione format='json' per output machine-readable."
    )
)
def skillsmp_search(
    q: str,
    category: Optional[str] = None,
    sort_by: Optional[str] = None,
    limit: int = 10,
    format: str = "text",
) -> str:
    """Keyword search su SkillsMP.

    Args:
        q: Query di ricerca (es. 'stripe payment', 'react components')
        category: Filtro categoria (es. 'payment', 'frontend', 'llm-ai', 'cicd')
        sort_by: Ordinamento — 'stars' (popolarita) o 'recent' (default)
        limit: Numero risultati (1-100, default 10)
        format: 'text' per output leggibile, 'json' per output strutturato
    """
    params = {"q": q, "limit": min(max(limit, 1), 100)}
    if category:
        params["category"] = category
    if sort_by:
        params["sortBy"] = sort_by

    try:
        data = _cached_or_fetch(f"search:{q}:{category}:{sort_by}", f"{API_BASE}/skills/search", params)
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"HTTP {e.response.status_code}", "message": str(e)})
    except httpx.RequestError as e:
        return json.dumps({"error": "connection_error", "message": str(e)})

    if not data.get("success"):
        return json.dumps({"error": "api_error", "message": str(data)})

    if format == "json":
        return _format_search_results_json(data)

    return _format_search_results(q, data, limit)


@mcp.tool(
    description=(
        "Ricerca semantica AI su SkillsMP. "
        "Usa Cloudflare AI per trovare skill pertinenti al significato. "
        "Opzione format='json' per output machine-readable."
    )
)
def skillsmp_ai_search(q: str, format: str = "text") -> str:
    """AI semantic search su SkillsMP.

    Args:
        q: Descrizione in linguaggio naturale (es. 'How to create a web scraper')
        format: 'text' o 'json'
    """
    try:
        data = _cached_or_fetch(f"ai:{q}", f"{API_BASE}/skills/ai-search", {"q": q})
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"HTTP {e.response.status_code}"})
    except httpx.RequestError as e:
        return json.dumps({"error": "connection_error", "message": str(e)})

    if not data.get("success"):
        return json.dumps({"error": "api_error", "message": str(data)})

    results = data.get("data", {}).get("data", [])
    if not results:
        return json.dumps({"skills": []}) if format == "json" else f"Nessun risultato per '{q}'."

    if format == "json":
        out = {
            "query": q,
            "results": [
                {
                    "name": r.get("skill", {}).get("name"),
                    "author": r.get("skill", {}).get("author"),
                    "stars": r.get("skill", {}).get("stars", 0),
                    "score": round(r.get("score", 0), 4),
                    "updated": _format_date(r.get("skill", {}).get("updatedAt", "")),
                    "description": r.get("skill", {}).get("description", ""),
                    "url": r.get("skill", {}).get("skillUrl", ""),
                }
                for r in results
            ],
            "rate_limit": {
                "remaining": _tracker.remaining(),
                "calls_today": _tracker.calls_today,
            }
        }
        return json.dumps(out, indent=2, ensure_ascii=False)

    lines = [f"## 🧠 Risultati AI Search per '{q}'", ""]
    for r in results:
        s = r.get("skill", {})
        score = r.get("score", 0)
        stars = s.get("stars", 0)
        updated = _format_date(s.get("updatedAt", ""))
        lines.append(f"### 🎯 {float(score):.0%} match | ⭐ {stars} | {s['name']} — by {s.get('author', '?')}")
        lines.append(f"   _{s.get('description', '')}_")
        lines.append(f"   📅 Aggiornato: {updated}")
        lines.append(f"   🔗 {s.get('skillUrl', '')}")
        lines.append("")

    return "\n".join(lines)


@mcp.tool(
    description=(
        "Cerca una skill specifica su SkillsMP e ne restituisce le statistiche. "
        "Utile per verificare se la versione locale e aggiornata. "
        "Opzione format='json' per output machine-readable."
    )
)
def skillsmp_check_skill(
    skill_name: str,
    author_hint: Optional[str] = None,
    format: str = "text",
) -> str:
    """Cerca una skill locale su SkillsMP e la confronta.

    Args:
        skill_name: Nome della skill (es. 'stripe-integration', 'supabase')
        author_hint: Suggerimento autore per filtrare (es. 'stripe', 'vercel')
        format: 'text' o 'json'
    """
    params = {"q": skill_name.replace("-", " "), "limit": 10, "sortBy": "stars"}
    try:
        data = _cached_or_fetch(f"check:{skill_name}", f"{API_BASE}/skills/search", params)
    except (httpx.HTTPStatusError, httpx.RequestError) as e:
        return json.dumps({"error": str(e)})

    skills = data.get("data", {}).get("skills", [])
    if not skills:
        return json.dumps({"found": False, "skill_name": skill_name}) if format == "json" else \
               f"Nessuna skill trovata per '{skill_name}' su SkillsMP."

    if author_hint:
        hint_lower = author_hint.lower()
        filtered = [s for s in skills if hint_lower in s.get("author", "").lower() or hint_lower in s.get("name", "").lower()]
        if filtered:
            skills = filtered

    if format == "json":
        out = {
            "skill_name": skill_name,
            "found": True,
            "results": [
                {
                    "name": s.get("name"),
                    "author": s.get("author"),
                    "stars": s.get("stars", 0),
                    "updated": _format_date(s.get("updatedAt", "")),
                    "description": s.get("description", ""),
                    "url": s.get("skillUrl", ""),
                }
                for s in skills[:5]
            ],
            "rate_limit": {
                "remaining": _tracker.remaining(),
                "calls_today": _tracker.calls_today,
            }
        }
        return json.dumps(out, indent=2, ensure_ascii=False)

    lines = [f"## 🔎 Risultati per '{skill_name}' su SkillsMP", ""]
    for s in skills[:5]:
        stars = s.get("stars", 0)
        updated = _format_date(s.get("updatedAt", ""))
        lines.append(f"### ⭐ {stars} | {s['name']} — by {s.get('author', '?')}")
        lines.append(f"   _{s.get('description', '')}_")
        lines.append(f"   📅 Aggiornato: {updated}  |  🔗 {s.get('skillUrl', '')}")
        lines.append("")

    return "\n".join(lines)


@mcp.tool(
    description=(
        "Confronta una skill locale con le alternative su SkillsMP, "
        "ordinate per popolarita. Opzione format='json' per output machine-readable."
    )
)
def skillsmp_compare_skills(
    skill_name: str,
    local_stars: int = 0,
    format: str = "text",
) -> str:
    """Confronta skill locale con alternative su SkillsMP.

    Args:
        skill_name: Nome della skill locale
        local_stars: Stelle GitHub della skill locale (default 0)
        format: 'text' o 'json'
    """
    params = {"q": skill_name.replace("-", " "), "limit": 8, "sortBy": "stars"}
    try:
        data = _cached_or_fetch(f"compare:{skill_name}", f"{API_BASE}/skills/search", params)
    except (httpx.HTTPStatusError, httpx.RequestError) as e:
        return json.dumps({"error": str(e)})

    skills = data.get("data", {}).get("skills", [])
    if not skills:
        return json.dumps({"found": False, "skill_name": skill_name}) if format == "json" else \
               f"Nessuna alternativa trovata per '{skill_name}'."

    if format == "json":
        out = {
            "skill_name": skill_name,
            "local_stars": local_stars,
            "alternatives": [
                {
                    "name": s.get("name"),
                    "author": s.get("author"),
                    "stars": s.get("stars", 0),
                    "updated": _format_date(s.get("updatedAt", "")),
                    "is_better": s.get("stars", 0) > local_stars,
                    "description": s.get("description", ""),
                    "url": s.get("skillUrl", ""),
                }
                for s in skills[:6]
            ],
            "rate_limit": {
                "remaining": _tracker.remaining(),
                "calls_today": _tracker.calls_today,
            }
        }
        return json.dumps(out, indent=2, ensure_ascii=False)

    lines = [
        f"## 📊 Confronto: '{skill_name}'",
        f"**Skill locale:** ⭐ {local_stars}",
        f"**Skill trovate su SkillsMP:** {len(skills)}",
        "",
    ]
    for i, s in enumerate(skills[:6], 1):
        stars = s.get("stars", 0)
        updated = _format_date(s.get("updatedAt", ""))
        label = "MIGLIORE" if stars > local_stars else "SIMILE" if stars == local_stars else "MENO POPOLARE"
        lines.append(f"**{i}. {'⭐' if stars > local_stars else '↔'} {label}** {s['name']} by {s.get('author', '?')} (⭐ {stars})")
        lines.append(f"   _{s.get('description', '')}_")
        lines.append(f"   📅 {updated}")

    return "\n".join(lines)


@mcp.tool(
    description=(
        "Scansiona un intero dominio di skill locali su SkillsMP. "
        "Il dominio corrisponde a uno dei 17 del catalogo (es. '3. AI & AGENTS', '7. SECURITY'). "
        "Restituisce per ogni skill: stelle, data aggiornamento, autore. "
        "Opzione format='json' per output machine-readable."
    )
)
def skillsmp_scan_domain(
    domain_query: str,
    format: str = "text",
) -> str:
    """Scansiona tutte le skill di un dominio su SkillsMP.

    Args:
        domain_query: Nome o numero del dominio (es. '3', 'AI & AGENTS', '7. SECURITY')
        format: 'text' o 'json'
    """
    structure = _load_skill_structure()
    if not structure.get("domains"):
        return json.dumps({"error": "skill structure not found", "hint": "run generate_xlsx.py first"})

    # Trova il dominio per match parziale
    q = domain_query.lower().strip().rstrip(".")
    domain = None
    for d in structure["domains"]:
        key = f"{d.get('number', '')}. {d.get('name', '')}".lower()
        if q in key or q in d.get("name", "").lower() or q in str(d.get("number", "")):
            domain = d
            break

    if not domain:
        return json.dumps({"error": f"dominio '{domain_query}' non trovato",
                           "available": [f"{d.get('number')}. {d.get('name')}" for d in structure["domains"]]})

    # Raccogli tutte le skill del dominio
    all_skills = []
    for sub in domain.get("subdomains", []):
        for sk in sub.get("skills", []):
            if isinstance(sk, str):
                all_skills.append({"name": sk, "subdomain": sub.get("name", "")})
            else:
                all_skills.append({"name": sk["name"], "subdomain": sub.get("name", "")})

    if format == "json":
        results = []
        for sk in all_skills:
            try:
                data = _cached_or_fetch(f"check:{sk['name']}", f"{API_BASE}/skills/search",
                                         {"q": sk["name"].replace("-", " "), "limit": 3, "sortBy": "stars"})
                skills = data.get("data", {}).get("skills", [])
                if skills:
                    s = skills[0]
                    results.append({
                        "name": sk["name"],
                        "subdomain": sk["subdomain"],
                        "stars": s.get("stars", 0),
                        "author": s.get("author", ""),
                        "updated": _format_date(s.get("updatedAt", "")),
                        "url": s.get("skillUrl", ""),
                    })
                else:
                    results.append({"name": sk["name"], "subdomain": sk["subdomain"],
                                    "stars": 0})
            except:
                results.append({"name": sk["name"], "subdomain": sk["subdomain"], "error": "failed"})

        out = {
            "domain": f"{domain.get('number')}. {domain.get('name')}",
            "skills_checked": len(results),
            "skills": results,
            "rate_limit": {
                "remaining": _tracker.remaining(),
                "calls_today": _tracker.calls_today,
            }
        }
        return json.dumps(out, indent=2, ensure_ascii=False)

    # Formato testo
    lines = [f"## 📋 Scansione Dominio: {domain.get('number')}. {domain.get('name')}",
             f"Skill da verificare: {len(all_skills)}",
             f"📊 {_tracker.summary()}", ""]

    for sk in all_skills:
        try:
            data = _cached_or_fetch(f"check:{sk['name']}", f"{API_BASE}/skills/search",
                                     {"q": sk["name"].replace("-", " "), "limit": 3, "sortBy": "stars"})
            skills = data.get("data", {}).get("skills", [])
            if skills:
                s = skills[0]
                stars = s.get("stars", 0)
                updated = _format_date(s.get("updatedAt", ""))
                author = s.get("author", "")
                lines.append(f"  {sk['name']:40s}  ⭐ {int(stars):>6,}  📅 {updated}  👤 {author[:25]:25s}")
            else:
                lines.append(f"  {sk['name']:40s}  [non trovata su SkillsMP]")
        except:
            lines.append(f"  {sk['name']:40s}  [errore]")

    lines.append("")
    lines.append(f"✅ Verificate {len(all_skills)} skill — {_tracker.summary()}")
    return "\n".join(lines)


@mcp.tool(
    description=(
        "Scansiona le skill installate localmente in .agents/skills/ e rigenera "
        "skill_structure.json. Opzione format='json' per output machine-readable."
    )
)
def skillsmp_refresh_structure(
    dry_run: bool = False,
    format: str = "text",
) -> str:
    """Rigenera skill_structure.json dalle skill locali.

    Args:
        dry_run: Se True, mostra solo anteprima senza salvare
        format: 'text' o 'json'
    """
    if not os.path.exists(REFRESH_SCRIPT):
        return json.dumps({"error": f"refresh script not found: {REFRESH_SCRIPT}"})

    import subprocess
    cmd = [sys.executable, REFRESH_SCRIPT]
    if dry_run:
        cmd.append("--dry-run")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            return json.dumps({"error": result.stderr.strip()})

        output = result.stdout.strip()
        if format == "json":
            # Ricarica struttura
            if os.path.exists(SKILL_STRUCTURE_PATH):
                with open(SKILL_STRUCTURE_PATH, "r", encoding="utf-8") as f:
                    structure = json.load(f)
            else:
                structure = {"domains": []}

            total = sum(len(s["skills"]) for d in structure.get("domains", [])
                        for s in d.get("subdomains", []))
            return json.dumps({
                "success": True,
                "domains": len(structure.get("domains", [])),
                "skills": total,
                "dry_run": dry_run,
                "message": "struttura aggiornata" if not dry_run else "anteprima"
            }, indent=2, ensure_ascii=False)

        return output
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "refresh script timed out"})
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool(
    description=(
        "Mostra lo stato del sistema: chiamate API SkillsMP rimanenti oggi, "
        "numero di cache entries, health dell'API SkillsMP e skill installate localmente."
    )
)
def skillsmp_status() -> str:
    """Mostra lo stato del sistema SkillsMP.

    Restituisce: chiamate API, cache, health, skill locali
    """
    import datetime as dt

    # Health SkillsMP
    api_healthy = False
    api_error = ""
    try:
        h = httpx.get("https://skillsmp.com/api/health", timeout=5)
        api_healthy = h.status_code == 200 and h.json().get("status") == "ok"
    except Exception as e:
        api_error = str(e)

    # Skill locali
    local_count = 0
    agents_dir = os.path.expanduser("~/.agents/skills")
    if os.path.isdir(agents_dir):
        local_count = len([d for d in os.listdir(agents_dir)
                          if os.path.isdir(os.path.join(agents_dir, d)) and
                          os.path.isfile(os.path.join(agents_dir, d, "SKILL.md"))])

    # Struttura
    structure_skills = 0
    if os.path.exists(SKILL_STRUCTURE_PATH):
        try:
            with open(SKILL_STRUCTURE_PATH, "r", encoding="utf-8") as f:
                struct = json.load(f)
            structure_skills = sum(len(s["skills"]) for d in struct.get("domains", [])
                                   for s in d.get("subdomains", []))
        except:
            pass

    now = dt.datetime.now()
    reset_time = now + dt.timedelta(days=1)
    reset_time = reset_time.replace(hour=0, minute=0, second=0)
    hours_to_reset = (reset_time - now).total_seconds() / 3600

    result = {
        "api_health": {
            "healthy": api_healthy,
            "error": api_error if api_error else None,
        },
        "rate_limit": {
            "remaining": _tracker.remaining(),
            "calls_today": _tracker.calls_today,
            "daily_limit": _tracker.daily_limit,
            "reset_in_hours": round(hours_to_reset, 1),
        },
        "cache": {
            "entries": len(_cache),
            "ttl_seconds": DEFAULT_TTL,
        },
        "skills_local": {
            "installed": local_count,
            "in_structure": structure_skills,
        },
        "server_version": SERVER_VERSION,
    }

    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool(
    description=(
        "Confronta una skill locale con la versione su SkillsMP. "
        "Legge la SKILL.md locale, cerca su SkillsMP, e confronta le descrizioni. "
        "Restituisce: IDENTICA, SIMILE o DIVERSA con dettagli."
    )
)
def skillsmp_skill_diff(
    skill_name: str,
    format: str = "text",
) -> str:
    """Confronta skill locale con versione SkillsMP.

    Args:
        skill_name: Nome della skill (es. 'stripe-integration')
        format: 'text' o 'json'
    """
    # 1. Leggi descrizione locale
    local_desc = ""
    local_path = os.path.join(SKILLS_DIR, skill_name, "SKILL.md")
    if os.path.exists(local_path):
        try:
            with open(local_path, "r", encoding="utf-8") as f:
                content = f.read()
            import re
            m = re.search(r'description:\s*"([^"]*)"', content)
            if m:
                local_desc = m.group(1)
            if not local_desc:
                m = re.search(r'description:\s*([^\n]+)', content)
                if m:
                    local_desc = m.group(1).strip()
        except:
            pass

    # 2. Cerca su SkillsMP
    try:
        data = _cached_or_fetch(f"diff:{skill_name}", f"{API_BASE}/skills/search",
                                 {"q": skill_name.replace("-", " "), "limit": 5, "sortBy": "stars"})
    except Exception as e:
        return json.dumps({"error": str(e)})

    skills = data.get("data", {}).get("skills", [])
    if not skills:
        return json.dumps({"skill_name": skill_name, "found": False}) if format == "json" else \
               f"Skill '{skill_name}' non trovata su SkillsMP."

    # Prendi la prima (piu' stelline)
    remote = skills[0]
    remote_desc = remote.get("description", "")
    remote_stars = remote.get("stars", 0)
    remote_updated = _format_date(remote.get("updatedAt", ""))
    remote_author = remote.get("author", "")
    remote_url = remote.get("skillUrl", "")

    # 3. Confronto
    local_normalized = local_desc.lower().strip()[:100]
    remote_normalized = remote_desc.lower().strip()[:100]

    if not local_desc:
        status = "SOLO_REMOTE"
        score = 0
    elif local_normalized == remote_normalized:
        status = "IDENTICA"
        score = 1.0
    elif local_normalized[:50] == remote_normalized[:50]:
        status = "SIMILE"
        score = 0.7
    else:
        # Similarita' per parole condivise
        local_words = set(local_normalized.split())
        remote_words = set(remote_normalized.split())
        if local_words and remote_words:
            intersection = local_words & remote_words
            union = local_words | remote_words
            score = len(intersection) / len(union) if union else 0
        else:
            score = 0

        if score >= 0.5:
            status = "SIMILE"
        else:
            status = "DIVERSA"

    if format == "json":
        return json.dumps({
            "skill_name": skill_name,
            "found": True,
            "status": status,
            "similarity_score": round(score, 2),
            "local": {"description": local_desc[:150] if local_desc else "(non disponibile)"},
            "remote": {
                "name": remote.get("name"),
                "author": remote_author,
                "stars": remote_stars,
                "updated": remote_updated,
                "description": remote_desc[:150],
                "url": remote_url,
            },
        }, indent=2, ensure_ascii=False)

    # Formato testo
    icon = {"IDENTICA": "✅", "SIMILE": "🟡", "DIVERSA": "🔴", "SOLO_REMOTE": "ℹ️"}.get(status, "❓")
    lines = [
        f"## {icon} skillsmp_skill_diff: '{skill_name}'",
        f"**Stato:** {status} (score: {score:.0%})",
        "",
        f"**Locale:** {local_desc[:120] if local_desc else '(nessuna descrizione locale)'}",
        "",
        f"**SkillsMP:** by {remote_author} | ⭐ {remote_stars} | 📅 {remote_updated}",
        f"   {remote_desc[:150]}",
        f"   🔗 {remote_url}",
    ]
    lines.append("")
    if status == "IDENTICA":
        lines.append("   ✅ Descrizione identica — skill allineata.")
    elif status == "DIVERSA":
        lines.append("   ⚠️ Descrizione diversa — verificare se la skill locale e' aggiornata.")
    
    return "\n".join(lines)


@mcp.tool(
    description=(
        "Scansiona TUTTE le skill locali e produce un report prioritizzato "
        "delle piu' obsolete rispetto a SkillsMP. "
        "Ordina per differenza di popolarita' (stelle SkillsMP vs stima locale). "
        "Opzione --domain per limitare a un dominio specifico."
    )
)
def skillsmp_check_outdated(
    domain: Optional[str] = None,
    limit: int = 20,
    min_stars: int = 1000,
    format: str = "text",
) -> str:
    """Trova le skill locali piu' obsolete su SkillsMP.

    Args:
        domain: Filtra per dominio (es. '7. SECURITY')
        limit: Max risultati (default 20, max 100)
        min_stars: Stelle minime SkillsMP per considerare la skill (default 1000)
        format: 'text' o 'json'
    """
    # Carica struttura
    if not os.path.exists(SKILL_STRUCTURE_PATH):
        return json.dumps({"error": "skill_structure.json not found"})

    with open(SKILL_STRUCTURE_PATH, "r", encoding="utf-8") as f:
        struct = json.load(f)

    # Raccogli tutte le skill (filtrate per dominio)
    all_skills = []
    for dom in struct.get("domains", []):
        dn = f"{dom.get('number', '')}. {dom['name']}"
        if domain and domain.lower() not in dn.lower() and domain.lower() not in dom['name'].lower():
            continue
        for sub in dom.get("subdomains", []):
            for sk in sub.get("skills", []):
                all_skills.append({"name": sk, "domain": dn, "subdomain": sub["name"]})

    if not all_skills:
        return json.dumps({"error": f"nessuna skill trovata per dominio '{domain}'"})

    # Verifica su SkillsMP
    outdated = []
    for i, sk in enumerate(all_skills):
        try:
            data = _cached_or_fetch(f"out:{sk['name']}", f"{API_BASE}/skills/search",
                                     {"q": sk["name"].replace("-", " "), "limit": 3, "sortBy": "stars"})
            skills = data.get("data", {}).get("skills", [])
            if skills:
                s = skills[0]
                stars = s.get("stars", 0)
                updated = _format_date(s.get("updatedAt", ""))
                author = s.get("author", "")
                if stars >= min_stars:
                    outdated.append({
                        "name": sk["name"],
                        "domain": sk["domain"],
                        "stars": stars,
                        "updated": updated,
                        "author": author,
                        "url": s.get("skillUrl", ""),
                    })
        except:
            pass

    # Ordina per stelle (decrescente)
    outdated.sort(key=lambda x: x["stars"], reverse=True)
    outdated = outdated[:min(max(limit, 1), 100)]

    if format == "json":
        return json.dumps({
            "domain_filter": domain or "all",
            "skills_checked": len(all_skills),
            "outdated_found": len(outdated),
            "skills": outdated,
            "rate_limit": {
                "remaining": _tracker.remaining(),
                "calls_today": _tracker.calls_today,
            }
        }, indent=2, ensure_ascii=False)

    lines = [
        f"## 📊 Report Skill Obsolete",
        f"Dominio: {domain or 'TUTTI'} | Verificate: {len(all_skills)} | Candidate obsolete: {len(outdated)}",
        f"📊 {_tracker.summary()}",
        "",
    ]
    for sk in outdated[:limit]:
        lines.append(f"  {sk['name']:45s}  ⭐ {int(sk['stars']):>6,}  📅 {sk['updated']}  👤 {sk['author'][:25]:25s}")
    lines.append("")
    lines.append(f"🏆 Le {min(limit, len(outdated))} skill piu' popolari su SkillsMP (da considerare per update)")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════
#  Avvio (con auto-refresh struttura)
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Auto-refresh condizionale
    import subprocess
    _needs_refresh = AUTO_REFRESH

    if _needs_refresh and os.path.exists(SKILL_STRUCTURE_PATH):
        # Controlla se la struttura ha piu' di 1 ora
        try:
            with open(SKILL_STRUCTURE_PATH, "r", encoding="utf-8") as f:
                _existing = json.load(f)
            _meta = _existing.get("_meta", {})
            _last = _meta.get("last_refresh", "")
            if _last:
                _last_dt = datetime.datetime.fromisoformat(_last)
                _age_hours = (datetime.datetime.now() - _last_dt).total_seconds() / 3600
                if _age_hours < 1:
                    _needs_refresh = False
        except:
            pass

    if _needs_refresh and os.path.exists(REFRESH_SCRIPT):
        try:
            result = subprocess.run(
                [sys.executable, REFRESH_SCRIPT, "--merge"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                if os.path.exists(SKILL_STRUCTURE_PATH):
                    with open(SKILL_STRUCTURE_PATH, "r", encoding="utf-8") as f:
                        _loaded_structure = json.load(f)
            print(f"[SkillsMP v{SERVER_VERSION}] Auto-refresh: {'OK' if result.returncode == 0 else 'FAILED'}")
            if result.returncode != 0:
                print(f"  Error: {result.stderr.strip()}")
        except Exception as e:
            print(f"[SkillsMP] Auto-refresh error: {e}")
    else:
        print(f"[SkillsMP v{SERVER_VERSION}] Auto-refresh: saltato (struttura recente)")

    # Conta tools per print
    _tool_count = len(mcp._tool_manager.list_tools())
    print(f"[SkillsMP v{SERVER_VERSION}] Server avviato con {_tool_count} tools")
    mcp.run(transport="stdio")
