param(
    [string]$Version
)

if (-not $Version) {
    Write-Host "Usage: ./release.ps1 1.6.8"
    exit 1
}

$Tag = "v$Version"
$Repo = "Hunterkilla1018/Life_RPG"

$FullZip = "LifeRPG_full.zip"
$PatchZip = "LifeRPG_patch.zip"
$Manifest = "manifest.json"

Write-Host "====================================="
Write-Host " Releasing LifeRPG $Version"
Write-Host "====================================="

# ----------------------------------------
# Clean
# ----------------------------------------
Write-Host "Cleaning build folders..."
if (Test-Path dist) { Remove-Item -Recurse -Force dist }
if (Test-Path build) { Remove-Item -Recurse -Force build }

# ----------------------------------------
# Build Launcher
# ----------------------------------------
Write-Host "Building Launcher..."
$env:LAUNCHER_VERSION = $Tag
pyinstaller LifeRPG_Launcher.spec --clean -y
if ($LASTEXITCODE -ne 0) { exit 1 }

# ----------------------------------------
# Build Game
# ----------------------------------------
Write-Host "Building Game..."
pyinstaller LifeRPG_Game.spec --clean -y
if ($LASTEXITCODE -ne 0) { exit 1 }

# ----------------------------------------
# Verify Game Build
# ----------------------------------------
if (!(Test-Path "dist\LifeRPG.exe") -and !(Test-Path "dist\LifeRPG")) {
    Write-Error "Game build not detected in dist folder."
    exit 1
}

# ----------------------------------------
# Generate Manifest
# ----------------------------------------
Write-Host "Generating manifest..."
python scripts/generate_manifest.py
if ($LASTEXITCODE -ne 0) { exit 1 }

# ----------------------------------------
# Create Full ZIP
# ----------------------------------------
Write-Host "Creating full ZIP..."
if (Test-Path $FullZip) { Remove-Item $FullZip }

# Zip everything in dist except launcher
$items = Get-ChildItem dist | Where-Object {
    $_.Name -notlike "LifeRPG_Launcher*"
}

Compress-Archive -Path $items.FullName `
                 -DestinationPath $FullZip `
                 -Force

# ----------------------------------------
# Create Patch (Option B)
# ----------------------------------------
Write-Host "Checking previous release for patch diff..."

$PreviousTag = gh release list --limit 2 --json tagName --jq ".[1].tagName"

if ($PreviousTag) {

    Write-Host "Previous release: $PreviousTag"

    if (Test-Path prev_manifest) { Remove-Item -Recurse -Force prev_manifest }
    mkdir prev_manifest

    gh release download $PreviousTag `
        --pattern manifest.json `
        --dir prev_manifest `
        --clobber

    if (Test-Path "prev_manifest/manifest.json") {

        $OldManifest = Get-Content "prev_manifest/manifest.json" | ConvertFrom-Json
        $NewManifest = Get-Content $Manifest | ConvertFrom-Json

        $ChangedFiles = @()

        foreach ($file in $NewManifest.files.PSObject.Properties.Name) {
            if ($OldManifest.files.$file -ne $NewManifest.files.$file) {

                # Detect onefile or folder mode
                if (Test-Path "dist\$file") {
                    $ChangedFiles += "dist\$file"
                }
                elseif (Test-Path "dist\LifeRPG\$file") {
                    $ChangedFiles += "dist\LifeRPG\$file"
                }
            }
        }

        if ($ChangedFiles.Count -gt 0) {
            Compress-Archive -Path $ChangedFiles `
                             -DestinationPath $PatchZip `
                             -Force

            Write-Host "Patch created with $($ChangedFiles.Count) changed files."
        }
        else {
            Write-Host "No changed files detected. Skipping patch."
        }
    }
    else {
        Write-Host "Previous manifest not found. Skipping patch."
    }

    Remove-Item -Recurse -Force prev_manifest
}
else {
    Write-Host "No previous release found. Skipping patch."
}

# ----------------------------------------
# Git Commit & Tag
# ----------------------------------------
Write-Host "Committing changes..."
git add .
git commit -m "Release $Version"

Write-Host "Tagging..."
git tag -a $Tag -m "LifeRPG $Version"

Write-Host "Pushing..."
git push origin main
git push origin $Tag

# ----------------------------------------
# Create Release
# ----------------------------------------
Write-Host "Creating GitHub release..."

gh release create $Tag `
    $FullZip `
    $Manifest `
    --repo $Repo `
    --title "LifeRPG $Version" `
    --notes "Automated release $Version"

if (Test-Path $PatchZip) {
    gh release upload $Tag $PatchZip --repo $Repo
}

Write-Host ""
Write-Host "====================================="
Write-Host " Release $Version complete."
Write-Host "====================================="
