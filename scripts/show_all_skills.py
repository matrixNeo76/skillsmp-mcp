"""
show_all_skills.py — Mostra tutte le skill locali con verifica SkillsMP.
Legge la struttura da skill_structure.json.

Uso:
  python show_all_skills.py
  SKILLSMP_API_KEY="..." python show_all_skills.py
"""
import sys, os, re, json, time
sys.stdout.reconfigure(encoding='utf-8')
os.environ['PYTHONIOENCODING'] = 'utf-8'

import httpx

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STRUCTURE_PATH = os.path.join(REPO_DIR, 'data', 'skill_structure.json')

with open(STRUCTURE_PATH, 'r', encoding='utf-8') as f:
    structure = json.load(f)

API_BASE = 'https://skillsmp.com/api/v1'
API_KEY = os.environ.get('SKILLSMP_API_KEY', '')

def search(q, limit=3):
    r = httpx.get(f'{API_BASE}/skills/search',
                  params={'q': q, 'limit': limit, 'sortBy': 'stars'},
                  headers={'Authorization': f'Bearer {API_KEY}'}, timeout=10)
    r.raise_for_status()
    return r.json()

# ── Scan ──
def check_skillsmp(skill_name):
    try:
        data = search(skill_name.replace('-', ' '), limit=1)
        if data.get('success') and data['data']['skills']:
            s = data['data']['skills'][0]
            stars = s.get('stars', 0)
            updated = s.get('updatedAt', '')
            if updated:
                updated = time.strftime('%Y-%m-%d', time.gmtime(int(updated)))
            author = s.get('author', '')
            return (int(stars), updated, author)
        return (0, '-', '-')
    except:
        return (-1, 'ERR', '')

total_skills = sum(len(sk) for d in structure['domains'] for sub in d['subdomains'] for sk in sub['skills'])
calls = 0
MAX_CALLS = 35

print('═' * 120)
print(f'  SKILL LOCALI — {total_skills} skill in {len(structure["domains"])} domini')
print('═' * 120)
print()

for domain in structure['domains']:
    dn = domain['name']
    dnum = domain.get('number', '')
    dom_total = sum(len(sub['skills']) for sub in domain['subdomains'])

    print(f'  {dnum}. {dn}')

    for sub in domain['subdomains']:
        print(f'     {sub["name"]} ({len(sub["skills"])})')
        for sk in sub['skills']:
            if calls < MAX_CALLS:
                stars, updated, author = check_skillsmp(sk)
                calls += 1
                if stars > 0:
                    star_str = f'{int(stars):>6,}'.replace(',', '.')
                    print(f'        {sk:45s}  ⭐{star_str}  📅{updated}  👤{author[:25]:25s}')
                else:
                    print(f'        {sk:45s}  [non trovata]')
            else:
                print(f'        {sk:45s}  [vedi catalogo]')
        print()
    print()

print(f'  {total_skills} skill totali | {calls} verificate su SkillsMP')
print(f'  Per rigenerare la struttura: python scripts/refresh_structure.py')
