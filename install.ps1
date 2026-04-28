# install.ps1 — Hermes ↔ AnythingLLM integration installer (Windows)
#
# What this does:
#   1. Copies the MCP server to %HERMES_HOME%\mcp_servers\
#   2. Copies the sync script to %HERMES_HOME%\scripts\
#   3. Registers the MCP server in %HERMES_HOME%\config.yaml
#   4. Appends the AnythingLLM fallback rule to %HERMES_HOME%\SOUL.md
#   5. Creates a Scheduled Task to sync sessions every 30 minutes
#
# Requirements:
#   - Hermes Agent installed (default: %USERPROFILE%\.hermes)
#   - AnythingLLM Desktop installed
#   - Run in PowerShell 5+ (or pwsh 7+)
#
# Usage (run as normal user — no admin needed):
#   Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
#   .\install.ps1

#Requires -Version 5

param(
    [string]$HermesHome = "",
    [string]$ApiKey = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Ok   { param($msg) Write-Host "✓ $msg" -ForegroundColor Green }
function Warn { param($msg) Write-Host "⚠ $msg" -ForegroundColor Yellow }
function Fail { param($msg) Write-Host "✗ $msg" -ForegroundColor Red; exit 1 }

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# ── Locate Hermes ──────────────────────────────────────────────────────────────
if (-not $HermesHome) {
    $HermesHome = if ($env:HERMES_HOME) { $env:HERMES_HOME } else { Join-Path $env:USERPROFILE ".hermes" }
}
if (-not (Test-Path $HermesHome)) {
    Fail "Hermes not found at $HermesHome. Set -HermesHome or install Hermes first."
}
Ok "Hermes found at $HermesHome"

# ── Locate Hermes venv Python ──────────────────────────────────────────────────
$VenvCandidates = @(
    (Join-Path $HermesHome "hermes-agent\venv\Scripts\python.exe"),
    (Join-Path $HermesHome "venv\Scripts\python.exe"),
    (Join-Path $HermesHome ".venv\Scripts\python.exe")
)
$VenvPython = $VenvCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $VenvPython) {
    Warn "Could not auto-detect Hermes venv Python."
    $VenvPython = Read-Host "Enter full path to Hermes venv python.exe"
    if (-not (Test-Path $VenvPython)) { Fail "Not found: $VenvPython" }
}
Ok "Python: $VenvPython"

# Verify mcp package
& $VenvPython -c "import mcp" 2>$null
if ($LASTEXITCODE -ne 0) {
    Fail "mcp package not found. Run: & '$VenvPython' -m pip install mcp"
}

# ── API key ────────────────────────────────────────────────────────────────────
if (-not $ApiKey) {
    $ApiKey = $env:ANYTHINGLLM_API_KEY
}
if (-not $ApiKey) {
    Write-Host ""
    Write-Host "AnythingLLM API key required."
    Write-Host "Find it in AnythingLLM Desktop -> Settings -> Tools -> API key"
    $SecureKey = Read-Host "API key" -AsSecureString
    $ApiKey = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecureKey))
}
if (-not $ApiKey) { Fail "API key is required." }
Ok "API key set"

# ── Create directories ─────────────────────────────────────────────────────────
$DirsToCreate = @("mcp_servers", "scripts", "logs")
foreach ($d in $DirsToCreate) {
    $path = Join-Path $HermesHome $d
    if (-not (Test-Path $path)) { New-Item -ItemType Directory -Path $path | Out-Null }
}

# ── Copy MCP server ────────────────────────────────────────────────────────────
$McpSrc  = Join-Path $ScriptDir "mcp\anythingllm-server.py"
$McpDest = Join-Path $HermesHome "mcp_servers\anythingllm-server.py"
Copy-Item $McpSrc $McpDest -Force
# Update shebang line (Windows ignores it but keeps the file consistent)
$content = Get-Content $McpDest -Raw
$content = $content -replace '^#!.*\n', "#!$VenvPython`n"
Set-Content $McpDest $content -NoNewline
Ok "MCP server installed -> $McpDest"

# ── Copy sync script ───────────────────────────────────────────────────────────
$SyncSrc  = Join-Path $ScriptDir "scripts\sync_sessions_to_anythingllm.py"
$SyncDest = Join-Path $HermesHome "scripts\sync_sessions_to_anythingllm.py"
Copy-Item $SyncSrc $SyncDest -Force
Ok "Sync script installed -> $SyncDest"

# ── Patch config.yaml ──────────────────────────────────────────────────────────
$Config = Join-Path $HermesHome "config.yaml"
if (-not (Test-Path $Config)) {
    Warn "config.yaml not found at $Config — skipping MCP registration."
    Warn "Add the following manually:"
    Get-Content (Join-Path $ScriptDir "config\mcp_config_snippet.yaml")
} else {
    $configText = Get-Content $Config -Raw
    if ($configText -match "anythingllm-data") {
        Warn "anythingllm-data already in config.yaml — skipping."
    } else {
        $McpBlock = @"

mcp_servers:
  anythingllm-data:
    enabled: true
    command: $VenvPython
    args:
      - $McpDest
    env: {}
"@
        if ($configText -match "(?m)^mcp_servers:") {
            $configText = $configText -replace "(?m)(^mcp_servers:\s*`n)", "`$1  anythingllm-data:`n    enabled: true`n    command: $([regex]::Escape($VenvPython))`n    args:`n      - $([regex]::Escape($McpDest))`n    env: {}`n"
        } else {
            $configText += $McpBlock
        }
        Set-Content $Config $configText -NoNewline
        Ok "config.yaml updated"
    }
}

# ── Patch SOUL.md ──────────────────────────────────────────────────────────────
$Soul = Join-Path $HermesHome "SOUL.md"
$RuleMarker = "AnythingLLM fallback"
$SoulSnippet = @"

**MANDATORY RULE — AnythingLLM fallback:**
When the user asks about personal information (dates, preferences, opinions, past conversations, projects, facts about themselves) and you do NOT find the answer in your built-in memory (USER.md / MEMORY.md), call these tools EXACTLY ONCE each — then stop and answer:
1. ``search_anythingllm_chats(query)`` — search past conversations
2. ``search_anythingllm_documents(query)`` — search stored documents

**STRICT LIMITS — do not break these:**
- Call each search tool AT MOST ONCE per user question. Do NOT retry with different keywords.
- After both calls return (even if empty), answer immediately with whatever you found.
- If both return no results, say so in one sentence and move on. Do not keep searching.
"@

if ((Test-Path $Soul) -and ((Get-Content $Soul -Raw) -match $RuleMarker)) {
    Warn "SOUL.md already contains AnythingLLM fallback rule — skipping."
} else {
    Add-Content $Soul $SoulSnippet
    Ok "SOUL.md updated with AnythingLLM fallback rule"
}

# ── Write .env ─────────────────────────────────────────────────────────────────
$EnvFile = Join-Path $HermesHome ".env"
$EnvEntry = "`n# AnythingLLM integration`nANYTHINGLLM_URL=http://localhost:3001`nANYTHINGLLM_API_KEY=$ApiKey`n"
if ((Test-Path $EnvFile) -and ((Get-Content $EnvFile -Raw) -match "ANYTHINGLLM_API_KEY")) {
    Warn ".env already has ANYTHINGLLM_API_KEY — not overwriting."
} else {
    Add-Content $EnvFile $EnvEntry
    Ok ".env updated with AnythingLLM credentials"
}

# ── Scheduled Task ─────────────────────────────────────────────────────────────
$TaskName = "HermesAnythingLLMSync"
$LogPath  = Join-Path $HermesHome "logs\sync.log"
$TaskCmd  = $VenvPython
$TaskArgs = "`"$SyncDest`""

$EnvBlock = "ANYTHINGLLM_API_KEY=$ApiKey;HERMES_HOME=$HermesHome;ANYTHINGLLM_URL=http://localhost:3001"

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Warn "Scheduled task '$TaskName' already exists — skipping."
} else {
    $action  = New-ScheduledTaskAction -Execute $TaskCmd -Argument $TaskArgs
    $trigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 30) -Once -At (Get-Date)
    $settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 5) -StartWhenAvailable

    # Set environment via registry workaround (Task Scheduler has no native env block)
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
        -Settings $settings -Description "Sync Hermes sessions to AnythingLLM every 30 min" | Out-Null

    # Patch env into task XML
    $TaskXml = (Get-ScheduledTask -TaskName $TaskName | Export-ScheduledTask)
    $EnvXml  = "<EnvironmentVariables><Variable><Name>ANYTHINGLLM_API_KEY</Name><Value>$ApiKey</Value></Variable><Variable><Name>HERMES_HOME</Name><Value>$HermesHome</Value></Variable></EnvironmentVariables>"
    if ($TaskXml -notmatch "EnvironmentVariables") {
        $TaskXml = $TaskXml -replace "</Exec>", "$EnvXml</Exec>"
        $TempXml = [System.IO.Path]::GetTempFileName() + ".xml"
        Set-Content $TempXml $TaskXml -Encoding UTF8
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Register-ScheduledTaskDefinition -TaskName $TaskName -Xml (Get-Content $TempXml -Raw) | Out-Null
        Remove-Item $TempXml
    }
    Ok "Scheduled task '$TaskName' created (every 30 minutes)"
}

# ── Initial sync ───────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "Running initial session sync..."
$env:ANYTHINGLLM_API_KEY = $ApiKey
$env:HERMES_HOME = $HermesHome
try {
    & $VenvPython $SyncDest
} catch {
    Warn "Initial sync failed (AnythingLLM may not be running). Re-run manually later."
}

Write-Host ""
Ok "Installation complete!"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Restart Hermes Agent"
Write-Host "  2. Run 'hermes mcp list' to verify anythingllm-data is active"
Write-Host "  3. Ask Hermes something it would only know from past conversations"
Write-Host ""
Write-Host "Manual sync: `$env:ANYTHINGLLM_API_KEY='...' ; & '$VenvPython' '$SyncDest'"
Write-Host "Re-sync all: `$env:ANYTHINGLLM_API_KEY='...' ; & '$VenvPython' '$SyncDest' --all"
