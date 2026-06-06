@echo off
REM ============================================================
REM   @matteofights Jarvis - one-click launcher
REM   Double-click this file. It starts the backend + dashboard
REM   and opens Jarvis in your browser. No terminal needed.
REM ============================================================

cd /d "%~dp0"
title @matteofights Jarvis launcher

REM Use the Windows trust store so Node/npm don't hit cert errors.
REM Spawned windows inherit this, so it also covers the agent at runtime.
set "NODE_OPTIONS=--use-system-ca"

REM --- First run: install dependencies if they're missing ---
if not exist "backend\node_modules" (
  echo Installing backend dependencies ^(first run, ~1 min^)...
  call npm --prefix backend install
)
if not exist "dashboard\node_modules" (
  echo Installing dashboard dependencies ^(first run, ~1 min^)...
  call npm --prefix dashboard install
)

REM --- Start each server in its own window (inherits this cwd + NODE_OPTIONS) ---
start "Jarvis backend" cmd /k "cd backend && npm run dev"
start "Jarvis dashboard" cmd /k "cd dashboard && npm run dev"

REM --- Give the dashboard a few seconds to boot, then open it ---
echo.
echo Starting Jarvis... opening your browser shortly.
timeout /t 6 /nobreak >nul
start "" http://localhost:5173

echo.
echo Jarvis is running in two windows. Close them to stop it.
echo You can close THIS window now.
timeout /t 3 /nobreak >nul
