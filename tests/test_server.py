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
