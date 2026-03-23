# Apply classic branch protection: require three CI status checks on the current default branch.
# Prerequisites: GitHub CLI (`gh`), auth via `gh auth login` OR env `GH_TOKEN` / `GITHUB_TOKEN`
# (PAT: classic `repo` scope, or fine-grained with Administration read/write on the repo).
# Usage (repo root): powershell -File scripts/apply-branch-protection.ps1 [-Branch main]

param(
    [string] $Branch = ""
)

$ErrorActionPreference = "Stop"

function Resolve-GhExe {
    $cmd = Get-Command gh -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $default = "C:\Program Files\GitHub CLI\gh.exe"
    if (Test-Path $default) { return $default }
    throw "GitHub CLI (gh) not found. Install: winget install GitHub.cli"
}

$gh = Resolve-GhExe
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repoRoot

$hasToken = [bool]($env:GH_TOKEN -or $env:GITHUB_TOKEN)
if (-not $hasToken) {
    cmd.exe /c "`"$gh`" auth status >nul 2>&1"
    if ($LASTEXITCODE -ne 0) {
        throw "Not logged in. Run: gh auth login   OR set `$env:GH_TOKEN for this session (see TODO-branch-protection.md)"
    }
}

$remoteUrl = git config --get remote.origin.url
if (-not $remoteUrl) {
    throw "No git remote `origin`. Add: git remote add origin https://github.com/OWNER/REPO.git"
}

if ($remoteUrl -match 'github\.com[:/](?<owner>[^/]+)/(?<repo>[^/.]+)') {
    $owner = $Matches["owner"]
    $repo = ($Matches["repo"] -replace "\.git$", "")
}
else {
    throw "Could not parse owner/repo from origin: $remoteUrl"
}

if (-not $Branch) {
    $Branch = git branch --show-current
    if (-not $Branch) { $Branch = "main" }
}

# GitHub REST: required_status_checks uses "checks" with { "context": "..." } per check run name.
$body = @"
{
  "required_status_checks": {
    "strict": true,
    "checks": [
      { "context": "ci-web / web" },
      { "context": "ci-api / api" },
      { "context": "ci-contracts / contracts" }
    ]
  },
  "enforce_admins": false,
  "restrictions": null
}
"@

Write-Host "PUT repos/$owner/$repo/branches/$Branch/protection"
$body | & $gh api --method PUT "repos/$owner/$repo/branches/$Branch/protection" --input -
if ($LASTEXITCODE -ne 0) {
    throw "gh api failed. If checks are unknown, run workflows once on $Branch, then retry. Or use UI: docs/branch-protection.md"
}

Write-Host "[OK] Branch protection updated. Verify in GitHub: Settings -> Branches -> $Branch"
