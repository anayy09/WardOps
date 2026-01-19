# WardOps Setup Script for Windows
# Run this script to set up and start the backend

Write-Host "=== WardOps Backend Setup ===" -ForegroundColor Cyan

# Check if venv exists
if (-Not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate venv
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Run migrations
Write-Host "Running database migrations..." -ForegroundColor Yellow
alembic upgrade head

Write-Host ""
Write-Host "=== Setup Complete! ===" -ForegroundColor Green
Write-Host ""
Write-Host "To start the backend server, run:" -ForegroundColor Cyan
Write-Host "  uvicorn app.main:app --reload" -ForegroundColor White
Write-Host ""
Write-Host "To start Celery worker (optional), run in another terminal:" -ForegroundColor Cyan
Write-Host "  celery -A app.worker worker --loglevel=info --pool=solo" -ForegroundColor White
Write-Host ""
