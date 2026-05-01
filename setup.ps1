# setup.ps1 — Installa SkillsMP MCP Server + Skill per Craft Agents (Windows)
# Uso: powershell -ExecutionPolicy Bypass -File setup.ps1

$RepoDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AgentsDir = "$env:USERPROFILE\.agents"
$SkillsDir = "$AgentsDir\skills"
$McpJsonDst = "$env:USERPROFILE\.mcp.json"
$SkillSrc = "$RepoDir\skills\skillsmp-checker"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SkillsMP MCP — Installer (Windows)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ── 1. API Key ──
$apiKey = $env:SKILLSMP_API_KEY
if (-not $apiKey) {
    $apiKey = Read-Host "Inserisci la tua SkillsMP API key (lascia vuoto per dopo)"
}

# ── 2. Installa skill ──
Write-Host ">>> Installazione skill..." -ForegroundColor Yellow
if (-not (Test-Path $SkillsDir)) {
    New-Item -ItemType Directory -Path $SkillsDir -Force | Out-Null
}
if (Test-Path "$SkillsDir\skillsmp-checker") {
    Write-Host "  Skill gia presente, aggiorno..." -ForegroundColor Gray
    Remove-Item "$SkillsDir\skillsmp-checker" -Recurse -Force
}
Copy-Item -Path $SkillSrc -Destination "$SkillsDir\skillsmp-checker" -Recurse -Force
Write-Host "  Skill installata in $SkillsDir\skillsmp-checker\" -ForegroundColor Green

# ── 3. Configura .mcp.json ──
Write-Host ">>> Configurazione MCP server..." -ForegroundColor Yellow
$mcpConfig = @{
    mcpServers = @{
        skillsmp = @{
            command = "python"
            args = @("$RepoDir\server.py")
            env = @{
                SKILLSMP_API_KEY = $apiKey
            }
        }
    }
}

if (Test-Path $McpJsonDst) {
    Write-Host "  ~\.mcp.json gia esistente, unisco..." -ForegroundColor Gray
    Copy-Item $McpJsonDst "$McpJsonDst.bak" -Force
    $existing = Get-Content $McpJsonDst -Raw | ConvertFrom-Json
    if (-not $existing.mcpServers) {
        $existing | Add-Member -NotePropertyName "mcpServers" -NotePropertyValue @{}
    }
    $existing.mcpServers | Add-Member -NotePropertyName "skillsmp" -NotePropertyValue $mcpConfig.mcpServers.skillsmp -Force
    $existing | ConvertTo-Json -Depth 10 | Set-Content $McpJsonDst -Encoding UTF8
    Write-Host "  Unione completata" -ForegroundColor Green
} else {
    $mcpConfig | ConvertTo-Json -Depth 10 | Set-Content $McpJsonDst -Encoding UTF8
    Write-Host "  Creato nuovo .mcp.json" -ForegroundColor Green
}
Write-Host "  MCP server configurato in $McpJsonDst" -ForegroundColor Green

# ── 4. Verifica ──
Write-Host ""
Write-Host ">>> Verifica installazione..." -ForegroundColor Yellow
if (Test-Path "$SkillsDir\skillsmp-checker\SKILL.md") {
    Write-Host "  Skill: OK" -ForegroundColor Green
} else {
    Write-Host "  Skill: NON TROVATA" -ForegroundColor Red
}
if (Test-Path $McpJsonDst) {
    Write-Host "  MCP config: OK" -ForegroundColor Green
    $check = Get-Content $McpJsonDst -Raw | ConvertFrom-Json
    if ($check.mcpServers.skillsmp) {
        Write-Host "  skillsmp MCP server: registrato" -ForegroundColor Green
    } else {
        Write-Host "  skillsmp MCP server: NON TROVATO" -ForegroundColor Red
    }
} else {
    Write-Host "  MCP config: NON TROVATO" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Installazione completata!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Riavvia la sessione Craft Agent per caricare i tools." -ForegroundColor White
Write-Host "  Poi prova: skillsmp_check_skill('stripe-integration')" -ForegroundColor White
Write-Host ""
