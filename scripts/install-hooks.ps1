# install-hooks.ps1 — Installa git pre-commit hook per auto-refresh struttura
# Uso: powershell -ExecutionPolicy Bypass -File scripts/install-hooks.ps1

$RepoDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$HookPath = "$RepoDir\.git\hooks\pre-commit"

$HookContent = @'
#!/usr/bin/env python3
"""Pre-commit hook: refresh skill_structure.json prima di ogni commit."""
import sys, os, subprocess

repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
refresh_script = os.path.join(repo_dir, 'scripts', 'refresh_structure.py')

if os.path.exists(refresh_script):
    result = subprocess.run(
        [sys.executable, refresh_script, '--merge', '--dry-run'],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode == 0:
        # Aggiorna effettivamente il file
        result = subprocess.run(
            [sys.executable, refresh_script, '--merge'],
            capture_output=True, text=True, timeout=30
        )
        print('[pre-commit] skill_structure.json aggiornato')
        # Staging del file aggiornato
        subprocess.run(['git', 'add', 'data/skill_structure.json'],
                      capture_output=True)
    else:
        print(f'[pre-commit] WARNING: refresh fallito: {result.stderr.strip()}')
'@

Set-Content -Path $HookPath -Value $HookContent -Encoding UTF8
Write-Host "Pre-commit hook installato: $HookPath" -ForegroundColor Green
