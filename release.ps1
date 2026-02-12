Write-Host "=== LifeRPG Local Release Build ==="

# -----------------------------------
# Clean previous builds
# -----------------------------------
if (Test-Path build) { Remove-Item build -Recurse -Force }
if (Test-Path dist) { Remove-Item dist -Recurse -Force }
if (Test-Path package) { Remove-Item package -Recurse -Force }
if (Test-Path verify) { Remove-Item verify -Recurse -Force }

# -----------------------------------
# Ensure PyInstaller installed
# -----------------------------------
python -m pip install --upgrade pip
pip install pyinstaller

# -----------------------------------
# Build Launcher
# -----------------------------------
Write-Host "Building Launcher..."
pyinstaller LifeRPG_Launcher.spec --clean -y

if ($LASTEXITCODE -ne 0) {
    Write-Error "Launcher build failed"
    exit 1
}

# -----------------------------------
# Build Game (from LifeRPG.spec)
# -----------------------------------
Write-Host "Building Game..."
pyinstaller LifeRPG.spec --clean -y

if ($LASTEXITCODE -ne 0) {
    Write-Error "Game build failed"
    exit 1
}

# -----------------------------------
# Locate Game EXE
# -----------------------------------
Write-Host "Locating LifeRPG.exe..."
$exe = Get-ChildItem -Recurse dist -Filter LifeRPG.exe | Select-Object -First 1

if (-not $exe) {
    Write-Error "LifeRPG.exe not found in dist folder"
    exit 1
}

Write-Host "Found Game EXE at:" $exe.FullName

# -----------------------------------
# Create Install Package
# -----------------------------------
New-Item -ItemType Directory -Force -Path package | Out-Null
Copy-Item $exe.FullName package\LifeRPG.exe

Compress-Archive -Path package\* -DestinationPath dist\LifeRPG_full.zip -Force

if (!(Test-Path dist\LifeRPG_full.zip)) {
    Write-Error "ZIP was not created"
    exit 1
}

Write-Host "ZIP created successfully."

# -----------------------------------
# Generate Manifest
# -----------------------------------
Write-Host "Generating manifest..."
Expand-Archive dist\LifeRPG_full.zip verify -Force

$files = Get-ChildItem verify -Recurse -File
$manifest = @{ files = @{} }

foreach ($file in $files) {
    $rel = $file.FullName.Substring((Resolve-Path verify).Path.Length + 1)
    $hash = (Get-FileHash $file.FullName -Algorithm SHA256).Hash.ToLower()
    $manifest.files[$rel] = $hash
}

$manifest | ConvertTo-Json -Depth 5 | Set-Content -Path dist\manifest.json -Encoding utf8

Write-Host "Manifest generated:"
Get-Content dist\manifest.json

Write-Host "=== Local Release Build Complete ==="
