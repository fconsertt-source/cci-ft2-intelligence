# =========================================
# Windows Production Build Script - v3.0
# Guardian FT2 Intelligence (Hardened)
# Deterministic • CI-Ready • Reproducible
# =========================================

$ErrorActionPreference = "Stop"

# =========================================
# Resolve Project Root deterministically
# =========================================
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

Write-Host "`n📁 Project Root: $ProjectRoot" -ForegroundColor DarkGray

# Gate script (deterministic)
$GateScript = Join-Path $ProjectRoot "scripts\pre_release_check.py" # Updated to use pre_release_check.py

# =========================================
# Paths
# =========================================
$EntryScript = ".\src\presentation\cli\gui_main.py"
$DistPath = ".\dist\windows"
$BuildPath = ".\build"
$ReportJSON = ".\dist\build_readiness_report.json"
$ReportHTML = ".\dist\build_readiness_report.html"
$ChecksumFile = ".\dist\build_checksums.txt"
$HooksDir = ".\hooks"

# Timestamped build id
$BuildId = Get-Date -Format "yyyyMMdd-HHmmss"
Write-Host "🏷️ Build ID: $BuildId" -ForegroundColor DarkCyan

# =========================================
# Preflight checks
# =========================================
Write-Host "`n🔍 Preflight checks..." -ForegroundColor Cyan

if (!(Test-Path $GateScript)) {
    Write-Host "❌ Gate script not found: $GateScript" -ForegroundColor Red
    exit 1
}

if (!(Test-Path $EntryScript)) {
    Write-Host "❌ Entry script not found: $EntryScript" -ForegroundColor Red
    exit 1
}

# =========================================
# Step 0: Detect REAL TCL/TK Paths (robust)
# =========================================
Write-Host "`n🔍 Detecting REAL TCL/TK paths..." -ForegroundColor Cyan

$pythonBase = python -c "import sys; print(sys.base_prefix)"

$tclDir = Join-Path $env:VIRTUAL_ENV "tcl\tcl8.6"
$tkDir  = Join-Path $env:VIRTUAL_ENV "tcl\tk8.6"

Write-Host "  Python Base: $pythonBase" -ForegroundColor Gray
Write-Host "  TCL Dir     : $tclDir" -ForegroundColor Gray
Write-Host "  TK Dir      : $tkDir" -ForegroundColor Gray

if (-not (Test-Path $tclDir)) { Write-Error "Tcl directory not found: $tclDir"; exit }
if (-not (Test-Path $tkDir)) { Write-Error "Tk directory not found: $tkDir"; exit }

# =========================================
# Step 1: Run Build Readiness Gate
# =========================================
Write-Host "`n🛡️ Running Pre-Release Check Gate..." -ForegroundColor Cyan # Updated message
python $GateScript
$gateExitCode = $LASTEXITCODE

switch ($gateExitCode) {
    2 {
        Write-Host "`n❌ CRITICAL: Build blocked!" -ForegroundColor Red
        Write-Host "💡 Check $ReportJSON for details" -ForegroundColor Yellow
        exit 1
    }
    1 {
        Write-Host "`n⚠️ WARNING: Build proceeding with warnings" -ForegroundColor Yellow
        Write-Host "💡 Review $ReportJSON before distribution" -ForegroundColor Yellow
    }
    0 {
        Write-Host "`n✅ Build readiness gate passed" -ForegroundColor Green
    }
}

# =========================================
# Step 2: Clean previous build (deterministic)
# =========================================
Write-Host "`n🧹 Cleaning previous builds..." -ForegroundColor Cyan

if (Test-Path $DistPath)  { Remove-Item $DistPath -Recurse -Force }
if (Test-Path $BuildPath) { Remove-Item $BuildPath -Recurse -Force }

New-Item -ItemType Directory -Force -Path $DistPath | Out-Null
New-Item -ItemType Directory -Force -Path $BuildPath | Out-Null

Write-Host "`n🔍 Detecting REAL TCL/TK paths..." -ForegroundColor Cyan

$pythonBase = python -c "import sys; print(sys.base_prefix)"

$tclDir = Join-Path $pythonBase "tcl\tcl8.6"
$tkDir  = Join-Path $pythonBase "tcl\tk8.6"

Write-Host "  Python Base: $pythonBase" -ForegroundColor Gray
Write-Host "  TCL Dir     : $tclDir" -ForegroundColor Gray
Write-Host "  TK Dir      : $tkDir" -ForegroundColor Gray

if (-not (Test-Path $tclDir)) {
    Write-Host "❌ TCL directory not found!" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $tkDir)) {
    Write-Host "❌ TK directory not found!" -ForegroundColor Red
    exit 1
}

# =========================================
# Step 3: PyInstaller build
# =========================================
Write-Host "`n🏗️ Running PyInstaller..." -ForegroundColor Cyan

pyinstaller `
    --onefile `
    --name "GuardianFT2" `
    --distpath $DistPath `
    --workpath $BuildPath `
    --noconfirm `
    --add-data "$tclDir;tcl/tcl8.6" `
    --add-data "$tkDir;tcl/tk8.6" `
    --collect-all=tkinter `
    --hidden-import=tkinter `
    --hidden-import=tkinter.ttk `
    --hidden-import=tkinter.filedialog `
    --hidden-import=tkinter.messagebox `
    --clean `
    $EntryScript

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ PyInstaller build failed!" -ForegroundColor Red
    exit 1
}

# =========================================
# Step 4: Generate SHA256 checksums
# =========================================
Write-Host "`n🔐 Generating SHA256 checksums..." -ForegroundColor Cyan

if (Test-Path $ChecksumFile) { Remove-Item $ChecksumFile -Force }

Get-ChildItem -Path $DistPath -Filter *.exe | ForEach-Object {
    $hash = Get-FileHash $_.FullName -Algorithm SHA256
    "$($_.Name) : $($hash.Hash)" | Out-File -Append -Encoding UTF8 $ChecksumFile
}

Write-Host "✅ Checksums saved to $ChecksumFile"

# =========================================
# Step 5: Generate HTML report
# =========================================
Write-Host "`n📄 Generating HTML report..." -ForegroundColor Cyan

$jsonData = Get-Content $ReportJSON | ConvertFrom-Json

$blockersHtml = ""
if ($jsonData.blockers) {
    $blockersHtml = ($jsonData.blockers | ForEach-Object { "<li>$_</li>" }) -join "`n"
}

$warningsHtml = ""
if ($jsonData.warnings) {
    $warningsHtml = ($jsonData.warnings | ForEach-Object { "<li>$_</li>" }) -join "`n"
}

$htmlContent = @"
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8">
<title>Guardian Build Readiness Report</title>
<style>
body { font-family: Segoe UI, Tahoma; direction: rtl; padding: 20px; }
.status { font-size: 24px; font-weight: bold; }
.success { color: green; }
.warning { color: orange; }
.error { color: red; }
pre { background: #f4f4f4; padding: 10px; border-radius: 5px; }
</style>
</head>
<body>
<h1>🛡️ Guardian Build Readiness Report</h1>
<p class="status">Status:
<span class="$($(if($jsonData.status -eq 'READY'){'success'}else{'error'}))">
$($jsonData.status)
</span></p>
<p>Exit Code: $($jsonData.exit_code)</p>
<p>Build ID: $BuildId</p>
<h2>Blockers ($($jsonData.blocker_count))</h2>
<ul>$blockersHtml</ul>
<h2>Warnings ($($jsonData.warning_count))</h2>
<ul>$warningsHtml</ul>
<h2>Checksums</h2>
<pre>$(Get-Content $ChecksumFile)</pre>
<p>Generated at $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")</p>
</body>
</html>
"@

$htmlContent | Out-File -Encoding UTF8 $ReportHTML
Write-Host "✅ HTML report saved to $ReportHTML"

# =========================================
# Step 6: Final Success
# =========================================
Write-Host "`n✅ Build complete!" -ForegroundColor Green
Write-Host "Executable: $DistPath\GuardianFT2.exe"
Write-Host "Checksums: $ChecksumFile"
Write-Host "Reports: $ReportJSON, $ReportHTML"
Write-Host "Build ID: $BuildId"
