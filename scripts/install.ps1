# DeepForge Installation Script for Windows
# Run with: powershell -ExecutionPolicy Bypass -File install.ps1

$ErrorActionPreference = "Stop"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  DeepForge Installation Script" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "Checking Python installation..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}
Write-Host "Found: $pythonVersion" -ForegroundColor Green

# Create virtual environment
Write-Host ""
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "Virtual environment already exists" -ForegroundColor Green
} else {
    python -m venv venv
    Write-Host "Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host ""
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host ""
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install --upgrade pip
pip install -e ".[dev]"
Write-Host "Dependencies installed" -ForegroundColor Green

# Create directories
Write-Host ""
Write-Host "Creating directories..." -ForegroundColor Yellow
$dirs = @(
    "$env:USERPROFILE\.deepforge\state\missions",
    "$env:USERPROFILE\.deepforge\logs",
    "$env:USERPROFILE\.deepforge\models",
    "$env:USERPROFILE\deepforge_workspaces"
)

foreach ($dir in $dirs) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "Created: $dir" -ForegroundColor Gray
    }
}
Write-Host "Directories created" -ForegroundColor Green

# Verify installation
Write-Host ""
Write-Host "Verifying installation..." -ForegroundColor Yellow
python -m interface.cli.deepforge --help | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Installation successful!" -ForegroundColor Green
} else {
    Write-Host "Installation verification failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Installation Complete!" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To get started:" -ForegroundColor White
Write-Host "  1. Activate the virtual environment:" -ForegroundColor Gray
Write-Host "     .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
Write-Host ""
Write-Host "  2. Start the web interface:" -ForegroundColor Gray
Write-Host "     deepforge serve" -ForegroundColor Yellow
Write-Host ""
Write-Host "  3. Or run a mission from CLI:" -ForegroundColor Gray
Write-Host "     deepforge run 'create a todo app'" -ForegroundColor Yellow
Write-Host ""






