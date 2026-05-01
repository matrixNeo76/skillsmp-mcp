"""
show_all_skills.py — Mostra skill locali con verifica SkillsMP.

Uso:
  python scripts/show_all_skills.py                     # Tutte le skill
  python scripts/show_all_skills.py --domain "7"        # Solo dominio 7
  python scripts/show_all_skills.py --domain "SECURITY" # Per nome
  python scripts/show_all_skills.py --outdated          # Solo candidate obsolete
  python scripts/show_all_skills.py --limit 10          # Max risultati
  python scripts/show_all_skills.py --format json       # Output JSON
"""
import sys, os, re, json, time, argparse
sys.stdout.reconfigure(encoding='utf-8')
os.environ['PYTHONIOENCODING'] = 'utf-8'

import httpx

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STRUCTURE_PATH = os.path.join(REPO_DIR, 'data', 'skill_structure.json')

with open(STRUCTURE_PATH, 'r', encoding='utf-8') as f:
    structure = json.load(f)

API_BASE = 'https://skillsmp.com/api/v1'
API_KEY = os.environ.get('SKILLSMP_API_KEY', '')

def fetch_skill(skill_name):
    try:
        r = httpx.get(f'{API_BASE}/skills/search',
                      params={'q': skill_name.replace('-', ' '), 'limit': 1, 'sortBy': 'stars'},
                      headers={'Authorization': f'Bearer {API_KEY}'}, timeout=10)
        data = r.json()
        skills = data.get('data', {}).get('skills', [])
        if skills:
            s = skills[0]
            stars = s.get('stars', 0)
            updated = s.get('updatedAt', '')
            if updated:
                updated = time.strftime('%Y-%m-%d', time.gmtime(int(updated)))
            return {'stars': int(stars), 'updated': updated, 'author': s.get('author', '')}
    except:
        pass
    return None

def main():
    parser = argparse.ArgumentParser(description='Mostra skill con verifica SkillsMP')
    parser.add_argument('--domain', help='Filtra per dominio (numero o nome)')
    parser.add_argument('--outdated', action='store_true', help='Solo skill candidate obsolete (stelle >1000)')
    parser.add_argument('--limit', type=int, default=0, help='Max risultati (0 = tutti)')
    parser.add_argument('--format', choices=['text', 'json'], default='text', help='Formato output')
    args = parser.parse_args()

    # Filtra skill
    all_skills = []
    for dom in structure['domains']:
        dn = f"{dom.get('number', '')}. {dom['name']}"
        if args.domain and args.domain.lower() not in dn.lower() and args.domain.lower() not in dom['name'].lower():
            continue
        for sub in dom['subdomains']:
            for sk in sub['skills']:
                all_skills.append({'name': sk, 'domain': dn, 'subdomain': sub['name']})

    if not all_skills:
        print(f'Nessuna skill trovata per dominio "{args.domain}"')
        return

    if args.limit:
        all_skills = all_skills[:args.limit]

    # Verifica su SkillsMP
    results = []
    for i, sk in enumerate(all_skills):
        data = fetch_skill(sk['name'])
        if data:
            results.append({**sk, **data})
        if args.format == 'text':
            progress = f'\r  Verificando {i+1}/{len(all_skills)}...'
            print(progress, end='', file=sys.stderr)

    if args.format == 'text':
        print('\r' + ' ' * 60 + '\r', end='', file=sys.stderr)

    # Filtra outdated se richiesto
    if args.outdated:
        results = [r for r in results if r.get('stars', 0) >= 1000]
        results.sort(key=lambda x: x['stars'], reverse=True)

    # Output
    if args.format == 'json':
        output = {
            'domain': args.domain or 'all',
            'total': len(results),
            'meta': structure.get('_meta', {}),
            'skills': results,
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        meta = structure.get('_meta', {})
        print(f'Skill: {len(results)}/{len(all_skills)} verificate')
        if meta:
            print(f'Struttura: v{meta.get("version", "?")}, refresh {meta.get("last_refresh", "?")[:19]}')
        print()
        for r in results:
            stars = r.get('stars', 0)
            updated = r.get('updated', '-')
            author = r.get('author', '')[:25]
            marker = '⭐' if stars >= 10000 else '📌' if stars >= 1000 else '  '
            print(f'  {marker} {r["name"]:45s}  ⭐{int(stars):>6,}  📅{updated}  👤{author}')
        print(f'\n{len(results)} skill mostrate')


if __name__ == '__main__':
    main()
