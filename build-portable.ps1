param([string]$Python='',[string]$OutputDir='outputs\single-exe')
$ErrorActionPreference='Stop'
$root=$PSScriptRoot
if(-not $Python){$Python=Join-Path $root '.venv\Scripts\python.exe'}
$env:TEMP=Join-Path $root 'work\portable-temp'
$env:TMP=$env:TEMP
$env:PYINSTALLER_CONFIG_DIR=Join-Path $root 'work\portable-pyinstaller-cache'
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'
$env:PATH="$(Split-Path $Python);$env:SystemRoot\System32;$env:SystemRoot"
New-Item -ItemType Directory -Force -Path $env:TEMP,$env:PYINSTALLER_CONFIG_DIR | Out-Null
& $Python -m PyInstaller --noconfirm --clean --onefile --windowed --noupx --name Stillpin --icon "$root\assets\Stillpin.ico" --add-data "$root\assets;assets" --paths "$root\src" --distpath $OutputDir --workpath "$root\work\portable-build" --specpath "$root\work" --exclude-module matplotlib --exclude-module pandas --exclude-module numpy --exclude-module scipy --exclude-module PyQt5 --exclude-module PyQt6 --exclude-module PySide6 "$root\src\app.py"
if($LASTEXITCODE -ne 0){throw 'Build failed'}
