#Requires -Version 5.1
<#
.SYNOPSIS
  Start the local Minecraft server and the playit.gg agent so friends can join over the internet.
#>
$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$CacheBin = Join-Path $Root ".cache\bin"
$Runtime = Join-Path $Root "runtime"
New-Item -ItemType Directory -Force -Path $CacheBin, $Runtime | Out-Null

$versions = @{}
Get-Content (Join-Path $Root "versions.conf") | ForEach-Object {
  if ($_ -match '^\s*#' -or $_ -notmatch '=') { return }
  $k, $v = $_.Split("=", 2)
  $versions[$k.Trim()] = $v.Trim()
}
$tag = $versions["PLAYIT_TAG"]
$port = $versions["SERVER_PORT"]

& (Join-Path $PSScriptRoot "Start-Server.ps1")

$playit = Join-Path $CacheBin "playit.exe"
if (-not (Test-Path $playit)) {
  Write-Host "Downloading playit $tag ..."
  $url = "https://github.com/playit-cloud/playit-agent/releases/download/$tag/playit-windows-x86_64.exe"
  Invoke-WebRequest -Uri $url -OutFile $playit
}

$secret = Join-Path $Runtime "playit.secret"
$log = Join-Path $Runtime "playit.log"
# Named pipe / socket lives next to the secret so the agent can start without
# a system runtime directory.
$socket = Join-Path $Runtime "playit.sock"
Start-Process -FilePath $playit -ArgumentList @("--secret-path", $secret, "--socket-path", $socket, "--log-path", $log)

Write-Host ""
Write-Host "Server is starting locally. Friends on the same Wi-Fi can use your LAN IP on port $port."
Write-Host "For internet friends:"
Write-Host "  1. Watch $log for a https://playit.gg/claim/... link, or wait for the playit window."
Write-Host "  2. Claim the agent in your browser."
Write-Host "  3. Add Tunnel -> Minecraft Java -> 127.0.0.1 port $port"
Write-Host "  4. Send friends the public address playit shows, not localhost."
