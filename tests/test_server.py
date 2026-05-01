"""
Test per SkillsMP MCP Server.
Esegui: pytest tests/ -v
"""
import sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from server import (
    RateLimitTracker, _format_date, _get_ttl, _format_search_results,
    DEFAULT_TTL, STABLE_TTL
)


def test_rate_limit_tracker():
    """RateLimitTracker deve tracciare correttamente le chiamate."""
    tracker = RateLimitTracker(daily_limit=100)
    assert tracker.remaining() == 100
    assert tracker.calls_today == 0
    assert tracker.is_near_limit(threshold=90) is False
    tracker.record_call()
    assert tracker.calls_today == 1
    assert tracker.remaining() == 99


def test_rate_limit_near_limit():
    """is_near_limit deve funzionare con threshold."""
    tracker = RateLimitTracker(daily_limit=100)
    # Simula 95 chiamate
    for _ in range(95):
        tracker.record_call()
    assert tracker.is_near_limit(threshold=10) is True
    assert tracker.is_near_limit(threshold=2) is False


def test_rate_limit_summary():
    """summary non deve crashare."""
    tracker = RateLimitTracker(daily_limit=500)
    s = tracker.summary()
    assert 'API calls today' in s
    assert '500' in s


def test_format_date_valid():
    """_format_date con timestamp valido."""
    ts = str(int(time.time()))
    result = _format_date(ts)
    # Deve essere una data YYYY-MM-DD
    parts = result.split('-')
    assert len(parts) == 3
    assert len(parts[0]) == 4


def test_format_date_empty():
    """_format_date con input vuoto."""
    assert _format_date('') == '-'
    assert _format_date(None) == '-'


def test_format_date_invalid():
    """_format_date con input invalido non crasha."""
    result = _format_date('abc')
    assert result is not None


def test_get_ttl_high_stars():
    """_get_ttl deve dare TTL piu lungo per skill con tante stelle."""
    data = {'data': {'skills': [{'stars': 5000}, {'stars': 200}]}}
    assert _get_ttl(data) == STABLE_TTL


def test_get_ttl_low_stars():
    """_get_ttl per skill con poche stelle."""
    data = {'data': {'skills': [{'stars': 50}]}}
    assert _get_ttl(data) == DEFAULT_TTL


def test_get_ttl_no_skills():
    """_get_ttl con lista vuota."""
    assert _get_ttl({'data': {'skills': []}}) == DEFAULT_TTL


def test_format_search_results_empty():
    """_format_search_results con skill vuote."""
    data = {'data': {'skills': []}}
    r = _format_search_results('test', data)
    assert 'Nessuna skill' in r


def test_structure_file_exists():
    """Il file skill_structure.json deve esistere e avere domini."""
    repo_dir = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(repo_dir, 'data', 'skill_structure.json')
    assert os.path.exists(path), f'File non trovato: {path}'

    with open(path, 'r', encoding='utf-8') as f:
        struct = json.load(f)

    assert 'domains' in struct
    assert len(struct['domains']) > 0
    assert struct['domains'][0].get('name')


def test_structure_has_skills():
    """Ogni dominio deve avere skill."""
    repo_dir = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(repo_dir, 'data', 'skill_structure.json')

    with open(path, 'r', encoding='utf-8') as f:
        struct = json.load(f)

    total = sum(len(s['skills']) for d in struct['domains'] for s in d['subdomains'])
    assert total > 500, f'Troppe poche skill: {total}'


def test_refresh_script_exists():
    """Il refresh script deve esistere."""
    repo_dir = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(repo_dir, 'scripts', 'refresh_structure.py')
    assert os.path.exists(path)


def test_xlsx_script_exists():
    """Lo script XLSX deve esistere."""
    repo_dir = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(repo_dir, 'scripts', 'generate_xlsx.py')
    assert os.path.exists(path)


def test_server_has_minimum_tools():
    """Il server deve avere almeno 9 tools MCP di base."""
    repo_dir = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, repo_dir)
    from server import mcp
    tools = [t.name for t in mcp._tool_manager.list_tools()]
    assert len(tools) >= 9
    base_expected = [
        'skillsmp_search', 'skillsmp_ai_search', 'skillsmp_check_skill',
        'skillsmp_compare_skills', 'skillsmp_scan_domain',
        'skillsmp_refresh_structure', 'skillsmp_status',
        'skillsmp_skill_diff', 'skillsmp_check_outdated',
    ]
    for e in base_expected:
        assert e in tools, f'Tool mancante: {e}'


def test_status_returns_json():
    """skillsmp_status deve restituire JSON valido."""
    repo_dir = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, repo_dir)
    from server import skillsmp_status
    import json
    result = json.loads(skillsmp_status())
    assert 'api_health' in result
    assert 'rate_limit' in result
    assert 'cache' in result
    assert 'skills_local' in result
    assert 'server_version' in result


def test_structure_has_meta():
    """skill_structure.json deve avere campo _meta."""
    repo_dir = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(repo_dir, 'data', 'skill_structure.json')
    with open(path, 'r', encoding='utf-8') as f:
        struct = json.load(f)
    assert '_meta' in struct, 'Mancante _meta'
    meta = struct['_meta']
    assert 'version' in meta
    assert 'last_refresh' in meta
    assert 'total_skills' in meta
    assert meta['total_skills'] > 500


def test_skill_diff_not_found():
    """skillsmp_skill_diff con skill inesistente non deve crashare."""
    repo_dir = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, repo_dir)
    from server import skillsmp_skill_diff
    import json
    # Skill che sicuramente non esiste
    result = skillsmp_skill_diff('questa-skill-non-esiste-mai', format='json')
    data = json.loads(result)
    assert 'error' in data or 'found' in data


def test_server_has_11_tools():
    """Il server deve avere 11 tools MCP."""
    repo_dir = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, repo_dir)
    from server import mcp
    tools = [t.name for t in mcp._tool_manager.list_tools()]
    assert len(tools) >= 11, f'Minimo 11 tools, trovati {len(tools)}'
    expected = ['skillsmp_discover', 'skillsmp_install_skill']
    for e in expected:
        assert e in tools, f'Nuovo tool mancante: {e}'


def test_server_version_file():
    """File VERSION deve contenere una versione valida."""
    repo_dir = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(repo_dir, 'VERSION')
    with open(path, 'r') as f:
        version = f.read().strip()
    parts = version.split('.')
    assert len(parts) == 3, f'Versione non semver: {version}'
    for p in parts:
        assert p.isdigit(), f'Parte non numerica: {p}'


def test_discover_returns_categories():
    """skillsmp_discover senza categoria deve restituire l'elenco."""
    repo_dir = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, repo_dir)
    from server import skillsmp_discover
    import json
    result = json.loads(skillsmp_discover(list_categories=True, format='json'))
    assert 'categories' in result
    assert 'llm-ai' in result['categories']


def test_persistent_cache_path():
    """La cache persistente deve avere un path valido."""
    repo_dir = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, repo_dir)
    from server import PERSISTENT_CACHE_PATH
    assert 'cache_skillsmp' in PERSISTENT_CACHE_PATH
    assert PERSISTENT_CACHE_PATH.endswith('.json')


def test_categories_dict():
    """SKILLSMP_CATEGORIES deve avere categorie note."""
    repo_dir = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, repo_dir)
    from server import SKILLSMP_CATEGORIES
    assert 'llm-ai' in SKILLSMP_CATEGORIES
    assert 'frontend' in SKILLSMP_CATEGORIES
    assert 'cloud' in SKILLSMP_CATEGORIES
    assert len(SKILLSMP_CATEGORIES) >= 40
