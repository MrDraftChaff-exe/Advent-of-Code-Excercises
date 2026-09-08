#Requires -Version 5.1
<#
.SYNOPSIS
  Install Java 25 if needed, download the vanilla Minecraft server, and start it.
#>
$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Runtime = Join-Path $Root "runtime"
$Cache = Join-Path $Root ".cache"
$Templates = Join-Path $Root "templates"
$VersionsFile = Join-Path $Root "versions.conf"

New-Item -ItemType Directory -Force -Path $Runtime, $Cache, (Join-Path $Cache "bin") | Out-Null

function Read-Versions {
  $map = @{}
  Get-Content $VersionsFile | ForEach-Object {
    if ($_ -match '^\s*#' -or $_ -notmatch '=') { return }
    $k, $v = $_.Split("=", 2)
    $map[$k.Trim()] = $v.Trim()
  }
  return $map
}

$V = Read-Versions
$McVersion = $V["MC_VERSION"]
$Sha1 = $V["MC_SERVER_SHA1"]
$JarUrl = $V["MC_SERVER_URL"]
$JavaMajor = [int]$V["JAVA_MAJOR"]
$Memory = $V["MC_MEMORY"]
$Port = $V["SERVER_PORT"]

function Get-JavaMajor([string]$JavaExe) {
  $output = & $JavaExe -version 2>&1 | Out-String
  if ($output -match 'version "([0-9]+)') { return [int]$Matches[1] }
  return 0
}

function Get-JavaExe {
  $cached = Join-Path $Cache "jdk\bin\java.exe"
  if (Test-Path $cached) { return $cached }
  $cmd = Get-Command java -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }
  return $null
}

function Install-Jdk {
  $existing = Get-JavaExe
  if ($existing) {
    $major = Get-JavaMajor $existing
    if ($major -ge $JavaMajor) {
      Write-Host "Java $major already available: $existing"
      return $existing
    }
  }
  Write-Host "Downloading Temurin JDK $JavaMajor for Windows x64..."
  $zip = Join-Path $Cache "jdk$JavaMajor.zip"
  $url = "https://api.adoptium.net/v3/binary/latest/$JavaMajor/ga/windows/x64/jdk/hotspot/normal/eclipse?project=jdk"
  Invoke-WebRequest -Uri $url -OutFile $zip
  $extract = Join-Path $Cache "jdk-extract"
  if (Test-Path $extract) { Remove-Item -Recurse -Force $extract }
  Expand-Archive -Path $zip -DestinationPath $extract -Force
  $home = Get-ChildItem -Path $extract -Directory | Select-Object -First 1
  $dest = Join-Path $Cache "jdk"
  if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }
  Move-Item $home.FullName $dest
  Remove-Item $zip -Force
  Remove-Item $extract -Recurse -Force -ErrorAction SilentlyContinue
  return (Join-Path $dest "bin\java.exe")
}

function Install-ServerJar {
  $jar = Join-Path $Cache "server-$McVersion.jar"
  $needDownload = $true
  if (Test-Path $jar) {
    $hash = (Get-FileHash -Algorithm SHA1 $jar).Hash.ToLower()
    if ($hash -eq $Sha1.ToLower()) { $needDownload = $false }
  }
  if ($needDownload) {
    Write-Host "Downloading Minecraft $McVersion server.jar..."
    Invoke-WebRequest -Uri $JarUrl -OutFile $jar
    $hash = (Get-FileHash -Algorithm SHA1 $jar).Hash.ToLower()
    if ($hash -ne $Sha1.ToLower()) {
      throw "SHA-1 mismatch for server.jar (got $hash, expected $Sha1)"
    }
  }
  Copy-Item $jar (Join-Path $Runtime "server.jar") -Force
}

function Seed-Runtime {
  foreach ($name in @("eula.txt", "server.properties")) {
    $dest = Join-Path $Runtime $name
    if (-not (Test-Path $dest)) {
      Copy-Item (Join-Path $Templates $name) $dest
    }
  }
}

$java = Install-Jdk
Install-ServerJar
Seed-Runtime

$serverJar = Join-Path $Runtime "server.jar"
Write-Host "Starting Minecraft $McVersion on port $Port ..."
Write-Host "Join at localhost  (Multiplayer -> Direct Connection)"
Start-Process -FilePath $java -WorkingDirectory $Runtime -ArgumentList @("-Xms1G", "-Xmx$Memory", "-jar", "server.jar", "nogui")
