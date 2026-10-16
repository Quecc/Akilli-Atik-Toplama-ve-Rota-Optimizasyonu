$ErrorActionPreference = 'Stop'
$taskPython = Get-Command python -ErrorAction SilentlyContinue
if (-not $taskPython) { Write-Host 'Python bulunamadi. Python 3.10 veya uzerini kurup PATH secenegini acin.'; exit 1 }
$taskUrl = 'http://127.0.0.1:4173'
$taskRunning = $false
try { $taskHealth = Invoke-RestMethod -Uri "$taskUrl/api/health" -TimeoutSec 1; $taskRunning = $taskHealth.app -eq 'temiz-rota' -and $taskHealth.engine -eq 'python' } catch {}
if (-not $taskRunning) {
  Start-Process -FilePath $taskPython.Source -ArgumentList @(('"' + (Join-Path $PSScriptRoot 'python/run_server.py') + '"')) -WorkingDirectory $PSScriptRoot -WindowStyle Hidden
  for ($taskAttempt = 0; $taskAttempt -lt 30; $taskAttempt++) {
    Start-Sleep -Milliseconds 200
    try { $taskHealth = Invoke-RestMethod -Uri "$taskUrl/api/health" -TimeoutSec 1; if ($taskHealth.app -eq 'temiz-rota' -and $taskHealth.engine -eq 'python') { $taskRunning = $true; break } } catch {}
  }
}
if (-not $taskRunning) { Write-Host 'Python sunucusu baslatilamadi. Terminalde python python/run_server.py ile hatayi gorebilirsiniz. 4173 portu doluysa --port 4174 kullanin.'; exit 1 }
Start-Process $taskUrl
