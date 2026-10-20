# Lets the GitHub edit worker + talking points run on Matteo's Claude subscription. Run once a year:
#   powershell -ExecutionPolicy Bypass -File tools\cloud\claude-token.ps1
# no "Stop" here: Windows PowerShell treats claude's normal stderr output as a fatal error
Set-Location (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent)

Write-Host ""
Write-Host "STEP 1: a browser window opens. Log in to Claude and click Authorize." -ForegroundColor Yellow
Write-Host "        If it shows a code instead, copy it and paste it back here, then press Enter." -ForegroundColor Yellow
Write-Host ""
& "$env:USERPROFILE\.local\bin\claude.exe" setup-token

Write-Host ""
Write-Host "STEP 2: above is a long line starting with sk-ant-oat01-" -ForegroundColor Yellow
$t = (Read-Host "        Copy that whole line, paste it here, press Enter").Trim()
if ($t -notmatch '^sk-ant-oat01-') {
    Write-Host "That isn't the token (it must start with sk-ant-oat01-). Run this again." -ForegroundColor Red
    exit 1
}

$env:GITHUB_TOKEN = $null; $env:GH_TOKEN = $null   # use gh's own login, not the limited token
& "C:\Program Files\GitHub CLI\gh.exe" secret set CLAUDE_CODE_OAUTH_TOKEN --repo fightingmatteo-ux/matteofights --body $t
Write-Host ""
Write-Host "DONE. The edit worker and talking points can now run. Tell Claude: token set" -ForegroundColor Green
