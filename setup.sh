#!/bin/bash
# setup.sh — Installa SkillsMP MCP Server + Skill per Craft Agents (Linux/macOS)
# Uso: bash setup.sh
# Per Windows: powershell -ExecutionPolicy Bypass -File setup.ps1

set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
AGENTS_DIR="$HOME/.agents"
SKILLS_DIR="$AGENTS_DIR/skills"
MCP_JSON_SRC="$REPO_DIR/docs/mcp.example.json"
MCP_JSON_DST="$HOME/.mcp.json"

echo "========================================"
echo "  SkillsMP MCP — Installer"
echo "========================================"
echo ""

# ── 1. API Key ──
if [ -z "$SKILLSMP_API_KEY" ]; then
    read -p "Inserisci la tua SkillsMP API key (lascia vuoto per dopo): " api_key
    if [ -n "$api_key" ]; then
        SKILLSMP_API_KEY="$api_key"
    fi
fi

# ── 2. Installa skill ──
echo ">>> Installazione skill..."
mkdir -p "$SKILLS_DIR"
if [ -d "$SKILLS_DIR/skillsmp-checker" ]; then
    echo "  Skill gia presente, aggiorno..."
fi
cp -r "$REPO_DIR/skills/skillsmp-checker" "$SKILLS_DIR/"
echo "  ✅ Skill installata in $SKILLS_DIR/skillsmp-checker/"

# ── 3. Configura .mcp.json ──
echo ">>> Configurazione MCP server..."
if [ -f "$MCP_JSON_DST" ]; then
    echo "  ~/.mcp.json gia esistente, unisco..."
    # Backup
    cp "$MCP_JSON_DST" "$MCP_JSON_DST.bak"
    # Unisci JSON (aggiungi skillsmp se non presente)
    python3 -c "
import json
with open('$MCP_JSON_DST') as f:
    cfg = json.load(f)
if 'mcpServers' not in cfg:
    cfg['mcpServers'] = {}
cfg['mcpServers']['skillsmp'] = {
    'command': 'python3',
    'args': ['$REPO_DIR/server.py'],
    'env': {'SKILLSMP_API_KEY': '$SKILLSMP_API_KEY'}
}
with open('$MCP_JSON_DST', 'w') as f:
    json.dump(cfg, f, indent=2)
print('  Unione completata')
" 2>&1
else
    python3 -c "
import json
cfg = {
    'mcpServers': {
        'skillsmp': {
            'command': 'python3',
            'args': ['$REPO_DIR/server.py'],
            'env': {'SKILLSMP_API_KEY': '$SKILLSMP_API_KEY'}
        }
    }
}
with open('$MCP_JSON_DST', 'w') as f:
    json.dump(cfg, f, indent=2)
print('  Creato nuovo .mcp.json')
" 2>&1
fi
echo "  ✅ MCP server configurato in $MCP_JSON_DST"

# ── 4. Verifica ──
echo ""
echo ">>> Verifica installazione..."
if [ -f "$SKILLS_DIR/skillsmp-checker/SKILL.md" ]; then
    echo "  ✅ Skill: OK"
else
    echo "  ❌ Skill: NON TROVATA"
fi
if [ -f "$MCP_JSON_DST" ]; then
    echo "  ✅ MCP config: OK"
    python3 -c "
import json
with open('$MCP_JSON_DST') as f:
    cfg = json.load(f)
if 'skillsmp' in cfg.get('mcpServers', {}):
    print('  ✅ skillsmp MCP server: registrato')
else:
    print('  ❌ skillsmp MCP server: NON TROVATO nel file')
" 2>&1
else
    echo "  ❌ MCP config: NON TROVATO"
fi
echo ""
echo "========================================"
echo "  Installazione completata!"
echo "========================================"
echo ""
echo "  Riavvia la sessione Craft Agent per caricare i tools."
echo "  Poi prova: skillsmp_check_skill('stripe-integration')"
echo ""
