# setup.ps1 — one-shot dev environment bootstrap (Windows)
# Usage: .\scripts\setup.ps1

$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot

Write-Host "=== SIRINAPHA Baan-Pla Link — Dev Setup ===" -ForegroundColor Cyan
Write-Host "Root: $ROOT"
Write-Host ""

# --- Frontend ---
Write-Host "[1/3] Frontend — npm install..." -ForegroundColor Yellow
Push-Location "$ROOT\frontend"
try {
    npm install
    if (-not (Test-Path ".env.local") -and (Test-Path ".env.local.example")) {
        Copy-Item ".env.local.example" ".env.local"
        Write-Host "  Created .env.local — please fill in keys" -ForegroundColor Green
    }
} finally {
    Pop-Location
}

# --- Backend ---
Write-Host "[2/3] Backend — Python venv + pip install..." -ForegroundColor Yellow
Push-Location "$ROOT\backend"
try {
    if (-not (Test-Path ".venv")) {
        python -m venv .venv
    }
    & ".venv\Scripts\pip" install --upgrade pip
    & ".venv\Scripts\pip" install -r lambda\requirements.txt
    & ".venv\Scripts\pip" install pytest hypothesis
} finally {
    Pop-Location
}

# --- Sanity Test ---
Write-Host "[3/3] Running sanity tests..." -ForegroundColor Yellow
Push-Location "$ROOT\backend"
try {
    & ".venv\Scripts\pytest" -q --tb=line
} finally {
    Pop-Location
}

Push-Location "$ROOT\frontend"
try {
    npm test
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "=== Setup complete ===" -ForegroundColor Cyan
Write-Host "Next:"
Write-Host "  cd frontend && npm run dev         # http://localhost:3000"
Write-Host "  cd backend && .venv\Scripts\pytest"
