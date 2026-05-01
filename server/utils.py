"""
utils.py — Utility functions per SkillsMP MCP Server.

Estratto da server.py per mantenere il file principale sotto controllo.
"""
import os
import re
import json
import time
import csv
import httpx
import datetime
from typing import Optional

# ══════════════════════════════════════════════════════════════════════
#  Rate Limit Tracker
# ══════════════════════════════════════════════════════════════════════

class RateLimitTracker:
    """Traccia le chiamate API SkillsMP giornaliere."""
    def __init__(self, daily_limit: int = 500):
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

    def is_near_limit(self, threshold: int = 50) -> bool:
        self._check_reset()
        return (self.daily_limit - self.calls_today) <= threshold

    def remaining(self) -> int:
        self._check_reset()
        if self.last_remaining is not None:
            return min(self.last_remaining, self.daily_limit - self.calls_today)
        return self.daily_limit - self.calls_today

    def summary(self) -> str:
        self._check_reset()
        return f"API calls today: {self.calls_today}/{self.daily_limit}, remaining: {self.remaining()}"


# ══════════════════════════════════════════════════════════════════════
#  Cache adattiva + persistente
# ══════════════════════════════════════════════════════════════════════

_cache: dict[str, tuple[float, dict]] = {}
DEFAULT_TTL = 300
STABLE_TTL = 600


def set_cache_ttls(default_ttl: int, stable_ttl: int):
    """Aggiorna TTL da config esterno."""
    global DEFAULT_TTL, STABLE_TTL
    DEFAULT_TTL = default_ttl
    STABLE_TTL = stable_ttl


def _get_ttl(data: dict) -> int:
    """TTL piu' lungo per skill stabili (tante stelle)."""
    skills = data.get("data", {}).get("skills", [])
    if skills:
        max_stars = max(s.get("stars", 0) for s in skills)
        if max_stars >= 1000:
            return STABLE_TTL
    return DEFAULT_TTL


class PersistentCache:
    """Cache su file JSON che sopravvive ai riavvii del server."""
    def __init__(self, path: str):
        self.path = path
        self.data = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
        except Exception:
            pass

    def get(self, key: str) -> Optional[dict]:
        entry = self.data.get(key)
        if entry and time.time() < entry.get("expires_at", 0):
            return entry.get("data")
        return None

    def set(self, key: str, data: dict, ttl: int):
        self.data[key] = {
            "data": data,
            "expires_at": time.time() + ttl,
            "cached_at": time.time(),
        }
        self._save()

    def count(self) -> int:
        return len(self.data)

    def clear_expired(self):
        now = time.time()
        self.data = {k: v for k, v in self.data.items()
                     if v.get("expires_at", 0) > now}
        self._save()


# ══════════════════════════════════════════════════════════════════════
#  HTTP call helpers
#  (istanziate da server.py con API_KEY e tracker)
# ══════════════════════════════════════════════════════════════════════

def make_api_call(url: str, params: dict, api_key: str,
                  tracker: RateLimitTracker, max_retries: int = 3,
                  request_timeout: int = 15) -> dict:
    """Chiamata API SkillsMP con retry, backoff e rate limit tracking."""
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    last_error = None
    for attempt in range(max_retries):
        try:
            resp = httpx.get(url, params=params, headers=headers, timeout=request_timeout)
            tracker.record_call(resp)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                wait = (2 ** attempt) * 5
                time.sleep(wait)
                last_error = e
                continue
            raise
        except httpx.RequestError as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
    raise last_error or httpx.RequestError("Max retries exceeded")


def cached_or_fetch(cache_key: str, url: str, params: dict,
                    api_key: str, tracker: RateLimitTracker,
                    max_retries: int = 3, request_timeout: int = 15,
                    persistent_cache: Optional[PersistentCache] = None) -> dict:
    """Helper con cache adattiva (in-memory + persistente su file)."""
    now = time.time()

    # Cache in-memory
    if cache_key in _cache:
        ts, data = _cache[cache_key]
        if now - ts < _get_ttl(data):
            return data

    # Cache persistente
    if persistent_cache:
        cached = persistent_cache.get(cache_key)
        if cached:
            _cache[cache_key] = (time.time(), cached)
            return cached

    try:
        data = make_api_call(url, params, api_key, tracker, max_retries, request_timeout)
        ttl = _get_ttl(data)
        _cache[cache_key] = (time.time(), data)
        if persistent_cache:
            persistent_cache.set(cache_key, data, ttl)
        return data
    except (httpx.HTTPStatusError, httpx.RequestError):
        if cache_key in _cache:
            return _cache[cache_key][1]
        if persistent_cache:
            cached = persistent_cache.get(cache_key)
            if cached:
                return cached
        raise


# ══════════════════════════════════════════════════════════════════════
#  Formattazione
# ══════════════════════════════════════════════════════════════════════

def format_date(updated: Optional[str]) -> str:
    """Converte timestamp SkillsMP in data YYYY-MM-DD."""
    if not updated:
        return "-"
    try:
        return datetime.datetime.fromtimestamp(int(updated)).strftime("%Y-%m-%d")
    except (ValueError, OSError):
        return str(updated)


def format_search_results(q: str, data: dict, tracker: RateLimitTracker,
                          limit: int = 10) -> str:
    """Formatta risultati ricerca in testo markdown."""
    skills = data.get("data", {}).get("skills", [])
    if not skills:
        return f"Nessuna skill trovata per '{q}'."
    pag = data.get("data", {}).get("pagination", {})
    total = pag.get("total", "?")
    rate_note = f"\n\n📊 {tracker.summary()}" if tracker.remaining() < 200 else ""
    lines = [f"## 🔍 Risultati per '{q}'  ({total} totali, mostrati {len(skills)}){rate_note}", ""]
    for s in skills:
        stars = s.get("stars", 0)
        updated = format_date(s.get("updatedAt", ""))
        lines.append(f"### ⭐ {stars} | {s['name']} — by {s.get('author', '?')}")
        lines.append(f"   _{s.get('description', '')}_")
        lines.append(f"   📅 Aggiornato: {updated}")
        lines.append(f"   🔗 {s.get('skillUrl', '')}")
        lines.append("")
    return "\n".join(lines)


def format_search_results_json(data: dict) -> str:
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
                "updated": format_date(s.get("updatedAt", "")),
                "description": s.get("description", ""),
                "url": s.get("skillUrl", ""),
            }
            for s in skills
        ],
    }
    return json.dumps(result, indent=2, ensure_ascii=False)


# ══════════════════════════════════════════════════════════════════════
#  Categorie SkillsMP
# ══════════════════════════════════════════════════════════════════════

SKILLSMP_CATEGORIES = {
    "payment": "Pagamenti e fatturazione",
    "ecommerce": "E-commerce",
    "sales-marketing": "Sales & Marketing",
    "project-management": "Project Management",
    "finance-investment": "Finance & Investment",
    "backend": "Backend Development",
    "frontend": "Frontend Development",
    "full-stack": "Full Stack",
    "mobile": "Mobile Development",
    "architecture-patterns": "Architecture Patterns",
    "gaming": "Game Development",
    "llm-ai": "LLM & AI",
    "machine-learning": "Machine Learning",
    "data-engineering": "Data Engineering",
    "data-analysis": "Data Analysis",
    "testing": "Testing",
    "security": "Security",
    "code-quality": "Code Quality",
    "cicd": "CI/CD",
    "cloud": "Cloud",
    "containers": "Containers",
    "devops": "DevOps",
    "git-workflows": "Git Workflows",
    "monitoring": "Monitoring",
    "sql-databases": "SQL Databases",
    "nosql-databases": "NoSQL Databases",
    "database-tools": "Database Tools",
    "smart-contracts": "Smart Contracts",
    "web3-tools": "Web3 Tools",
    "defi": "DeFi",
    "content-creation": "Content Creation",
    "design": "Design",
    "media": "Media",
    "documents": "Documents",
    "technical-docs": "Technical Docs",
    "education": "Education",
    "knowledge-base": "Knowledge Base",
    "productivity-tools": "Productivity & Integration",
    "automation-tools": "Automation Tools",
    "debugging": "Debugging",
    "system-admin": "System Administration",
    "cli-tools": "CLI Tools",
    "ide-plugins": "IDE Plugins",
    "domain-utilities": "Domain & DNS Tools",
}


# ══════════════════════════════════════════════════════════════════════
#  Skill description reader
# ══════════════════════════════════════════════════════════════════════

def read_local_skill_description(skill_name: str, skills_dir: str) -> str:
    """Legge la descrizione dalla SKILL.md locale."""
    local_path = os.path.join(skills_dir, skill_name, "SKILL.md")
    if not os.path.exists(local_path):
        return ""
    try:
        with open(local_path, "r", encoding="utf-8") as f:
            content = f.read()
        m = re.search(r'description:\s*"([^"]*)"', content)
        if m:
            return m.group(1)
        m = re.search(r'description:\s*([^\n]+)', content)
        if m:
            return m.group(1).strip()
    except Exception:
        pass
    return ""
