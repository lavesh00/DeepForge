# Kill process on port 8080
$port = 8080
$processes = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique

if ($processes) {
    foreach ($pid in $processes) {
        $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "Killing process: $($proc.ProcessName) (PID: $pid)" -ForegroundColor Yellow
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        }
    }
    Write-Host "Port $port is now free" -ForegroundColor Green
} else {
    Write-Host "No process found on port $port" -ForegroundColor Green
}






