# Silver Fox Production Service Restart Script
# Right-click this file and select "Run with PowerShell" (as Administrator)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Silver Fox Production Service Restart" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "[ERROR] This script requires Administrator privileges!" -ForegroundColor Red
    Write-Host "Please right-click this file and select 'Run as Administrator'" -ForegroundColor Yellow
    Write-Host ""
    pause
    exit 1
}

# Stop the service
Write-Host "[1/2] Stopping SilverFoxOrderProcessing service..." -ForegroundColor Yellow
try {
    Stop-Service -Name "SilverFoxOrderProcessing" -Force -ErrorAction Stop
    Write-Host "[OK] Service stopped successfully" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Failed to stop service: $_" -ForegroundColor Red
    pause
    exit 1
}

# Wait a moment for clean shutdown
Start-Sleep -Seconds 3

# Start the service
Write-Host "[2/2] Starting SilverFoxOrderProcessing service..." -ForegroundColor Yellow
try {
    Start-Service -Name "SilverFoxOrderProcessing" -ErrorAction Stop
    Write-Host "[OK] Service started successfully" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Failed to start service: $_" -ForegroundColor Red
    pause
    exit 1
}

# Verify service is running
Start-Sleep -Seconds 2
$service = Get-Service -Name "SilverFoxOrderProcessing"
if ($service.Status -eq "Running") {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "SUCCESS: Service restarted successfully" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Version 2.1.1 hotfix is now active!" -ForegroundColor Cyan
    Write-Host "Test the LIST order filtering at http://localhost:5000" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "[WARNING] Service status: $($service.Status)" -ForegroundColor Yellow
}

Write-Host ""
pause
