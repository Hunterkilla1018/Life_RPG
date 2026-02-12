param(
    [Parameter(Mandatory=$true)]
    [string]$Version
)

$owner = "Hunterkilla1018"
$repo = "Life_RPG"
$tag = "v$Version"

if (-not $env:GITHUB_TOKEN) {
    Write-Error "GITHUB_TOKEN environment variable not set."
    exit 1
}

Write-Host "Publishing $tag..."

# -----------------------------
# Commit changes
# -----------------------------
git checkout main
git pull origin main

git add .
git commit -m "Release $tag" 2>$null
git push origin main

# -----------------------------
# Create tag
# -----------------------------
git tag -a $tag -m "LifeRPG $tag"
git push origin $tag

# -----------------------------
# Create GitHub release
# -----------------------------
$headers = @{
    Authorization = "Bearer $env:GITHUB_TOKEN"
    Accept        = "application/vnd.github+json"
}

$body = @{
    tag_name = $tag
    name     = "LifeRPG $tag"
    body     = "Launcher $Version release."
    draft    = $false
    prerelease = $false
} | ConvertTo-Json

$url = "https://api.github.com/repos/$owner/$repo/releases"

$response = Invoke-RestMethod -Uri $url -Method Post -Headers $headers -Body $body

if ($response.id) {
    Write-Host "Release created successfully."
} else {
    Write-Error "Failed to create release."
    exit 1
}

Write-Host "Done. GitHub Actions should now start."
