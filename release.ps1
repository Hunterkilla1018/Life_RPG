param(
    [string]$Version
)

if (-not $Version) {
    Write-Host "Usage: ./release.ps1 1.5.2"
    exit
}

$Tag = "v$Version"
$Repo = "Hunterkilla1018/Life_RPG"
$FullZip = "LifeRPG_full.zip"
$PatchZip = "LifeRPG_patch.zip"
$ManifestFile = "manifest.json"

Write-Host "========================================="
Write-Host " Releasing Life RPG $Version"
Write-Host "========================================="

# ----------------------------
# CLEAN
# ----------------------------

if (Test-Path dist) { Remove-Item -Recurse -Force dist }
if (Test-Path build) { Remove-Item -Recurse -Force build }

# ----------------------------
# BUILD
# ----------------------------

pyinstaller LifeRPG.spec --clean -y
if ($LASTEXITCODE -ne 0) { exit }

# ----------------------------
# GENERATE MANIFEST
# ----------------------------

python generate_manifest.py
if ($LASTEXITCODE -ne 0) { exit }

# ----------------------------
# CREATE FULL ZIP
# ----------------------------

if (Test-Path $FullZip) { Remove-Item $FullZip }
Compress-Archive -Path dist\* -DestinationPath $FullZip

# ----------------------------
# CREATE PATCH ZIP
# ----------------------------

Write-Host "Checking for previous release..."

$PreviousTag = gh release list --limit 1 --json tagName --jq ".[0].tagName"

if ($PreviousTag) {

    Write-Host "Previous release: $PreviousTag"

    gh release download $PreviousTag --pattern manifest.json --dir prev_manifest

    $OldManifest = Get-Content "prev_manifest/manifest.json" | ConvertFrom-Json
    $NewManifest = Get-Content $ManifestFile | ConvertFrom-Json

    if (Test-Path $PatchZip) { Remove-Item $PatchZip }

    $ChangedFiles = @()

    foreach ($file in $NewManifest.files.PSObject.Properties.Name) {
        if ($OldManifest.files.$file -ne $NewManifest.files.$file) {
            $ChangedFiles += "dist\$file"
        }
    }

    if ($ChangedFiles.Count -gt 0) {
        Compress-Archive -Path $ChangedFiles -DestinationPath $PatchZip
        Write-Host "Patch zip created with $($ChangedFiles.Count) files."
    } else {
        Write-Host "No file changes detected. Skipping patch zip."
    }

    Remove-Item -Recurse -Force prev_manifest
}
else {
    Write-Host "No previous release found. Skipping patch."
}

# ----------------------------
# GIT
# ----------------------------

git add .
git commit -m "Release $Version"
git tag -a $Tag -m "Life RPG $Version"
git push origin main
git push origin $Tag

# ----------------------------
# CREATE RELEASE
# ----------------------------

gh release create $Tag `
    $FullZip `
    $ManifestFile `
    --repo $Repo `
    --title "Life RPG $Version" `
    --notes "Automated release $Version"

if (Test-Path $PatchZip) {
    gh release upload $Tag $PatchZip --repo $Repo
}

Write-Host ""
Write-Host "========================================="
Write-Host " Release $Version complete."
Write-Host "========================================="
