# Run Tideborn shore world build via UnrealEditor-Cmd (editor must be closed).
$ErrorActionPreference = "Stop"
$Project = "C:\Users\User\Desktop\AI\Grok\Tideborn\Tideborn.uproject"
$Script = "C:\Users\User\Desktop\AI\Grok\Tideborn\Tools\art\build_world.py"
$Result = "C:\Users\User\Desktop\AI\Grok\Tideborn\Tools\art\build_world_result.txt"
$LogDir = "C:\Users\User\Desktop\AI\Grok\Tideborn\Saved\Logs"

Write-Host "=== Tideborn run_build_world ==="

# Close editor if open
$procs = Get-Process -Name "UnrealEditor","UnrealEditor-Cmd" -ErrorAction SilentlyContinue
if ($procs) {
  Write-Host "Closing UnrealEditor processes: $($procs.Id -join ',')"
  $procs | Stop-Process -Force
  Start-Sleep -Seconds 5
}

# Locate UnrealEditor-Cmd for UE 5.4
$candidates = @(
  "C:\Program Files\Epic Games\UE_5.4\Engine\Binaries\Win64\UnrealEditor-Cmd.exe",
  "C:\Program Files\Epic Games\UE_5.5\Engine\Binaries\Win64\UnrealEditor-Cmd.exe",
  "C:\Program Files\Epic Games\UE_5.3\Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
)
$Cmd = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $Cmd) {
  $found = Get-ChildItem -Path "C:\Program Files\Epic Games" -Filter "UnrealEditor-Cmd.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($found) { $Cmd = $found.FullName }
}
if (-not $Cmd) { throw "UnrealEditor-Cmd.exe not found" }
if (-not (Test-Path $Project)) { throw "Missing project $Project" }
if (-not (Test-Path $Script)) { throw "Missing script $Script" }

Write-Host "Using $Cmd"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$outLog = Join-Path $LogDir "build_world_cmd.txt"

& $Cmd $Project `
  "-ExecutePythonScript=$Script" `
  -unattended -nosplash -NullRHI `
  2>&1 | Tee-Object -FilePath $outLog

Write-Host "ExitCode=$LASTEXITCODE"
if (Test-Path $Result) {
  Write-Host "---- build_world_result.txt ----"
  Get-Content $Result
} else {
  Write-Host "WARNING: result file missing at $Result"
}
