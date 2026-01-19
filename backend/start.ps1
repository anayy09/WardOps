# WardOps Start Script for Windows
# Starts the backend server

Write-Host "=== Starting WardOps Backend ===" -ForegroundColor Cyan

# Activate venv
if (Test-Path "venv\Scripts\Activate.ps1") {
    .\venv\Scripts\Activate.ps1
    Write-Host "Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "Virtual environment not found! Run setup.ps1 first." -ForegroundColor Red
    exit 1
}

# Start server
Write-Host "Starting FastAPI server on http://localhost:8000..." -ForegroundColor Yellow
Write-Host "API docs will be available at http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
