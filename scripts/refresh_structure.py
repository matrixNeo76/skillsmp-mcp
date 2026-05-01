"""
refresh_structure.py — Scansiona .agents/skills/ e rigenera skill_structure.json.

Uso:
  python refresh_structure.py                          # rigenera da zero
  python refresh_structure.py --merge                  # unisce con struttura esistente
  python refresh_structure.py --categorize-by-name     # auto-categorizza per nome skill
"""
import sys, os, re, json, argparse
sys.stdout.reconfigure(encoding='utf-8')
os.environ['PYTHONIOENCODING'] = 'utf-8'

AGENTS_SKILLS = os.path.expanduser('~/.agents/skills')
REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STRUCTURE_PATH = os.path.join(REPO_DIR, 'data', 'skill_structure.json')

# ── Mappa domini per parole chiave (per auto-categorizzazione) ──
DOMAIN_KEYWORDS = {
    '1. DEV ENGINEERING': {
        'keywords': ['javascript', 'typescript', 'python', 'go', 'rust', 'csharp', 'java', 'kotlin',
                     'react', 'vue', 'nextjs', 'next.', 'expo', 'shadcn', 'turborepo', 'nx-',
                     'monorepo', 'docker', 'mcp-server', 'mcp-', 'api-', 'openapi', 'swagger',
                     'stripe', 'paypal', 'migration', 'upgrade', 'async', 'error-', 'auth-',
                     'backend', 'frontend', 'full-stack', 'testing', 'e2e-', 'playwright',
                     'jest', 'vitest', 'cypress', 'nodejs', 'fastapi', 'spring', 'aspire',
                     'fluentui', 'dotnet', 'ef-core', 'nuget'],
        'subdomain_map': {
            'javascript': 'Linguaggi & Pattern', 'typescript': 'Linguaggi & Pattern',
            'python': 'Linguaggi & Pattern', 'go-': 'Linguaggi & Pattern',
            'rust': 'Linguaggi & Pattern', 'csharp': 'Linguaggi & Pattern',
            'error-': 'Linguaggi & Pattern', 'auth-': 'Linguaggi & Pattern',
            'react': 'Frontend Framework', 'vue': 'Frontend Framework',
            'nextjs': 'Frontend Framework', 'shadcn': 'Frontend Framework',
            'next-': 'Frontend Framework',
            'expo': 'Expo/React Native', 'native-': 'Expo/React Native',
            'turborepo': 'Monorepo & Build', 'nx-': 'Monorepo & Build',
            'monorepo': 'Monorepo & Build', 'docker': 'Monorepo & Build',
            'mcp-server': 'MCP Server Gen', 'mcp-': 'MCP Server Gen',
            'stripe': 'API Integration', 'paypal': 'API Integration', 'integrate-': 'API Integration',
            'migration': 'Migrazioni', 'upgrade': 'Migrazioni',
            'react18': 'Migrazioni', 'react19': 'Migrazioni',
            'angular': 'Migrazioni', 'dotnet-upgrade': 'Migrazioni',
            'fastapi': 'Backend Framework', 'nodejs': 'Backend Framework',
            'spring': 'Backend Framework', 'java-': 'Backend Framework',
            'kotlin-': 'Backend Framework', 'aspnet': 'Backend Framework',
            'dotnet-backend': 'Backend Framework',
            'api-': 'Backend Framework', 'openapi': 'Backend Framework',
            'microservices': 'Backend Framework', 'cqrs': 'Backend Framework',
            'saga-': 'Backend Framework',
        }
    },
    '2. INFRASTRUCTURE': {
        'keywords': ['k8s', 'kubernetes', 'helm', 'istio', 'linkerd', 'service-mesh', 'gitops',
                     'mtls', 'github-actions', 'gitlab-ci', 'deployment', 'devops', 'rollout',
                     'terraform', 'bicep', 'avm', 'azure-', 'aws-', 'gcp', 'multi-cloud', 'cost-optim',
                     'prometheus', 'grafana', 'distributed-tracing', 'slo', 'incident', 'runbook',
                     'on-call', 'postmortem'],
    },
    '3. AI & AGENTS': {
        'keywords': ['langchain', 'rag-', 'hybrid-search', 'embedding', 'similarity-search',
                     'vector-', 'prompt-', 'llm-', 'eval-', 'agentic', 'semantic-kernel',
                     'microsoft-agent', 'copilot-sdk', 'declarative-agents', 'workflow-orchestration',
                     'temporal', 'arize', 'phoenix', 'tavily', 'agent-governance', 'owasp',
                     'supply-chain'],
    },
    '4. GO-TO-MARKET': {
        'keywords': ['copywriting', 'copy-edit', 'content-strategy', 'social-content', 'cold-email',
                     'email-sequence', 'ad-creative', 'programmatic-seo', 'seo-audit', 'ai-seo',
                     'schema-markup', 'site-architecture', 'competitor', 'page-cro', 'signup-flow',
                     'onboarding', 'form-cro', 'popup-cro', 'paywall', 'ab-test', 'paid-ads',
                     'analytics', 'product-marketing', 'launch-strategy', 'pricing-strategy',
                     'marketing-', 'referral', 'lead-magnet', 'free-tool', 'competitive',
                     'sales-enablement', 'customer-research', 'gtm-', 'revops', 'churn-',
                     'billing-'],
    },
    '5. DESIGN & UI': {
        'keywords': ['design-', 'visual-design', 'tailwind', 'brand-', 'responsive-',
                     'frontend-design', 'ui-ux', 'ckm-', 'interaction', 'theme-', 'premium-frontend',
                     'web-design', 'web-artifact', 'accessibility', 'wcag', 'screen-reader',
                     'mobile-ios', 'mobile-android', 'penpot', 'excalidraw', 'canvas-design',
                     'algorithmic-art'],
    },
    '6. DATA & ANALYTICS': {
        'keywords': ['postgresql', 'sql-', 'supabase', 'cosmosdb', 'database', 'ef-core',
                     'dbt-', 'airflow', 'spark-', 'bigquery', 'ml-pipeline',
                     'powerbi', 'power-bi', 'kpi-', 'data-storytelling', 'fabric-lakehouse',
                     'data-quality', 'datanalysis', 'market-sizing', 'startup-financial',
                     'startup-metrics', 'dataverse'],
    },
    '7. SECURITY': {
        'keywords': ['security-review', 'sast-', 'secret-scanning', 'codeql', 'gdpr', 'pci-',
                     'secure-linux', 'openclaw', 'threat-model', 'stride', 'attack-tree',
                     'mitigation', 'solidity', 'nft-', 'defi-', 'web3-', 'binary-analysis',
                     'anti-reversing', 'protocol-reverse', 'memory-forensics'],
    },
    '8. MICROSOFT ECOSYSTEM': {
        'keywords': ['azure-', 'dotnet-', 'csharp', 'ef-core', 'nuget', 'fluentui', 'aspire',
                     'appinsights', 'winapp', 'winmd', 'winui3', 'msstore', 'electron',
                     'typespec', 'declarative-agents', 'mcp-create', 'flowstudio', 'power-apps',
                     'power-platform', 'cli-mastery', 'noob-mode', 'entra-', 'copilot-usage',
                     'microsoft-', 'mcp-copilot'],
    },
    '9. PROJECT & DOCS': {
        'keywords': ['documentation', 'doc-', 'readme', 'llms', 'adr', 'hads', 'tldr',
                     'specification', 'prd', 'epic-', 'feature-', 'implementation-plan',
                     'technical-spike', 'writing-plans', 'context-driven', 'context-map',
                     'track-management', 'workflow-patterns', 'worktrees', 'executing-plans',
                     'test-driven', 'refactor-plan', 'brainstorming', 'first-ask', 'boost-prompt',
                     'gh-cli', 'github-issues', 'git-commit', 'conventional-commit',
                     'git-advanced', 'git-flow', 'finishing-', 'make-repo', 'changelog',
                     'repo-story', 'draw-io', 'excalidraw', 'plantuml', 'blueprint-generator'],
    },
    '10. SYSTEMS & OPS': {
        'keywords': ['arch-linux', 'debian-linux', 'fedora-linux', 'centos-linux',
                     'bash-', 'shellcheck', 'bats-', 'uv-', 'hybrid-cloud',
                     'geofeed', 'deploy-to-vercel', 'vercel-cli', 'publish-to-pages',
                     'containerize'],
    },
    '11. BUSINESS & FINANCE': {
        'keywords': ['startup-', 'market-sizing', 'competitive-landscape', 'team-composition',
                     'employment', 'internal-comms', 'pricing-strategy', 'billing-', 'churn-'],
    },
    '12. CRAFT AGENT META': {
        'keywords': ['find-skills', 'skill-creator', 'writing-skills', 'make-skill-template',
                     'skills-cli', 'evaluation-methodology', 'suggest-awesome',
                     'prompt-builder', 'finalize-agent', 'create-agentsmd',
                     'copilot-instructions', 'remember', 'memory-merger',
                     'subagent', 'dispatching', 'parallel-', 'task-coordination',
                     'team-composition', 'team-communication', 'structured-autonomy',
                     'verification', 'systematic-debugging', 'parallel-debugging',
                     'doublecheck', 'code-review', 'review-and-refactor', 'skillsmp'],
    },
    '13. TESTING & QA': {
        'keywords': ['jest', 'vitest', 'pytest', 'mstest', 'xunit', 'nunit', 'tunit',
                     'junit', 'spring-boot-testing', 'unit-test', 'vue-testing',
                     'playwright', 'webapp-testing', 'scoutqa', 'polyglot-test',
                     'temporal-python', 'web3-testing', 'quality-playbook', 'ruff-'],
    },
    '14. SPECIALIZED': {
        'keywords': ['oracle-to-postgres', 'salesforce-apex', 'salesforce-component',
                     'salesforce-flow', 'convex-', 'better-auth', 'create-auth',
                     'email-and-password', 'two-factor', 'organization-best',
                     'snowflake', 'vercel-composition', 'vercel-react-',
                     'game-engine', 'godot', 'unity-'],
    },
    '15. CONTENT & MEDIA': {
        'keywords': ['docx', 'pptx', 'xlsx', 'pdf', 'pdftk', 'markdown-to-html',
                     'shuffle-json', 'convert-plaintext', 'transloadit',
                     'image-manipulation', 'slack-gif', 'nano-banana',
                     'email-drafter', 'email-sequence', 'cold-email'],
    },
    '16. GAMING & REVERSE': {
        'keywords': ['game-engine', 'godot', 'unity-ecs', 'binary-analysis',
                     'anti-reversing', 'memory-forensics', 'protocol-reverse',
                     'legacy-circuit', 'algorithmic-art'],
    },
    '17. UTILITY': {
        'keywords': ['agent-browser', 'agentcore', 'chrome-devtools', 'use-my-browser',
                     'slack', 'develop-userscripts', 'automate-this', 'autoresearch',
                     'daily-prep', 'roundup', 'meeting-minutes', 'dogfood', 'napkin',
                     'noob-mode', 'copilot-cli', 'what-context-needed',
                     'sandbox-npm', 'tzst', 'xdrop', 'xget', 'block-no-verify',
                     'editorconfig', 'finnish-humanizer', 'mkdocs-translations',
                     'readme-i18n', 'next-intl', 'refactor', 'quasi-coder',
                     'model-recommendation', 'running-claude-code', 'sponsor-finder',
                     'opensource-guide'],
    },
}


def extract_skill_info(skill_dir: str) -> dict:
    """Legge SKILL.md e restituisce nome + descrizione."""
    skill_name = os.path.basename(skill_dir)
    skill_path = os.path.join(skill_dir, 'SKILL.md')
    desc = ''
    if os.path.isfile(skill_path):
        try:
            with open(skill_path, 'r', encoding='utf-8') as f:
                content = f.read(2000)  # primi 2000 caratteri
            m = re.search(r'description:\s*"([^"]*)"', content)
            if m:
                desc = m.group(1)[:120]
            if not desc:
                m = re.search(r'description:\s*([^\n]+)', content)
                if m:
                    desc = m.group(1).strip()[:120]
        except:
            pass
    return {'name': skill_name, 'description': desc}


def categorize_skill(skill_name: str, existing_domains: list = None) -> tuple:
    """Categorizza una skill in (dominio, sottodominio) per parola chiave."""
    sn = skill_name.lower()
    
    # Cerca nei domini esistenti prima
    if existing_domains:
        for dom in existing_domains:
            for sub in dom.get('subdomains', []):
                if skill_name in sub.get('skills', []):
                    return (dom['name'], sub['name'])
    
    # Auto-categorizzazione per keyword
    for domain_key, domain_data in DOMAIN_KEYWORDS.items():
        for kw in domain_data['keywords']:
            if kw in sn or sn.startswith(kw) or sn.endswith(kw):
                # Estrai nome dominio senza numero
                dom_name = domain_key.split('. ', 1)[1]
                # Cerca sottodominio specifico
                sub_map = domain_data.get('subdomain_map', {})
                for sub_kw, sub_name in sub_map.items():
                    if sub_kw in sn or sn.startswith(sub_kw):
                        return (dom_name, sub_name)
                return (dom_name, 'Altro')
    
    return ('UTILITY', 'Varie')


def scan_and_build(merge: bool = False) -> dict:
    """Scansiona .agents/skills/ e costruisce struttura."""
    if not os.path.isdir(AGENTS_SKILLS):
        print(f'❌ Cartella non trovata: {AGENTS_SKILLS}')
        sys.exit(1)
    
    # Carica struttura esistente se merge
    existing = None
    if merge and os.path.isfile(STRUCTURE_PATH):
        try:
            with open(STRUCTURE_PATH, 'r', encoding='utf-8') as f:
                existing = json.load(f)
        except:
            pass
    
    # Scansiona directory skill
    all_skills = []
    for entry in sorted(os.listdir(AGENTS_SKILLS)):
        skill_dir = os.path.join(AGENTS_SKILLS, entry)
        if os.path.isdir(skill_dir) and os.path.isfile(os.path.join(skill_dir, 'SKILL.md')):
            info = extract_skill_info(skill_dir)
            all_skills.append(info)
    
    # Organizza per dominio
    domain_map = {}
    
    for sk in all_skills:
        dom_name, sub_name = categorize_skill(sk['name'], existing.get('domains') if existing else None)
        if dom_name not in domain_map:
            domain_map[dom_name] = {}
        if sub_name not in domain_map[dom_name]:
            domain_map[dom_name][sub_name] = []
        domain_map[dom_name][sub_name].append(sk['name'])
    
    # Costruisce output nel formato standard
    output = {'domains': []}
    for dom_name in sorted(domain_map.keys()):
        subs = []
        for sub_name in sorted(domain_map[dom_name].keys()):
            subs.append({'name': sub_name, 'skills': domain_map[dom_name][sub_name]})
        
        # Trova numero dominio
        dom_num = ''
        for dk in DOMAIN_KEYWORDS:
            if dk.endswith(dom_name):
                dom_num = dk.split('. ')[0]
                break
        
        output['domains'].append({
            'number': dom_num,
            'name': dom_name,
            'subdomains': subs
        })
    
    # Riordina domini per numero
    output['domains'].sort(key=lambda d: d.get('number', '99'))
    
    return output, all_skills


def save_structure(structure: dict):
    """Salva struttura su file JSON."""
    with open(STRUCTURE_PATH, 'w', encoding='utf-8') as f:
        json.dump(structure, f, indent=2, ensure_ascii=False)
    print(f'✅ Struttura salvata: {STRUCTURE_PATH}')
    total = sum(len(s['skills']) for d in structure['domains'] for s in d['subdomains'])
    print(f'   {len(structure["domains"])} domini, {total} skill')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scansiona skill e rigenera structure.json')
    parser.add_argument('--merge', action='store_true', help='Unisci con struttura esistente')
    parser.add_argument('--dry-run', action='store_true', help='Mostra risultato senza salvare')
    args = parser.parse_args()
    
    print(f'>>> Scansione {AGENTS_SKILLS}...')
    structure, skills = scan_and_build(merge=args.merge)
    print(f'   Trovate {len(skills)} skill')
    
    if args.dry_run:
        print('\nAnteprima per dominio:')
        for d in structure['domains']:
            cnt = sum(len(s['skills']) for s in d['subdomains'])
            print(f'  {d.get("number", "?")}. {d["name"]}: {cnt} skill')
            for s in d['subdomains']:
                print(f'      {s["name"]}: {len(s["skills"])}')
    else:
        save_structure(structure)
