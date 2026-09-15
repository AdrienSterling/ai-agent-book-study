<#
.SYNOPSIS
  Copy the Obsidian notes into the repo, optionally commit and push.

.EXAMPLE
  .\scripts\sync-notes.ps1
  .\scripts\sync-notes.ps1 -Message "ch1: notes + ReAct loop"
  .\scripts\sync-notes.ps1 -Message "ch2 day 1" -Push
#>
param(
    [string]$Message = "",
    [switch]$Push
)

$ErrorActionPreference = "Stop"

$src  = "C:\Users\dengl\OneDrive\Documents\AdrienSterlingObsidian\Knowledge\AI\Agent"
$repo = Split-Path $PSScriptRoot -Parent
$dst  = Join-Path $repo "notes"

if (-not (Test-Path $src)) { throw "Obsidian folder not found: $src" }
if (-not (Test-Path $dst)) { New-Item -ItemType Directory -Path $dst | Out-Null }

# markdown
$md = Get-ChildItem -Path $src -Filter *.md -File
foreach ($f in $md) {
    Copy-Item $f.FullName -Destination (Join-Path $dst $f.Name) -Force
    Write-Host "  notes/$($f.Name)"
}

# assets (images referenced by the notes)
$assetSrc = Join-Path $src "assets"
if (Test-Path $assetSrc) {
    $assetDst = Join-Path $dst "assets"
    if (-not (Test-Path $assetDst)) { New-Item -ItemType Directory -Path $assetDst | Out-Null }
    # copy the CONTENTS, not the folder itself - otherwise it nests assets/assets/
    Copy-Item (Join-Path $assetSrc "*") -Destination $assetDst -Recurse -Force
    $n = (Get-ChildItem $assetDst -Recurse -File).Count
    Write-Host "  notes/assets/ ($n files)"
}

Write-Host "synced $($md.Count) notes into $dst"

if ($Message -ne "") {
    Push-Location $repo
    try {
        git add -A
        $staged = git diff --cached --name-only
        if (-not $staged) {
            Write-Host "nothing to commit"
        } else {
            git commit -m $Message
            if ($?) { Write-Host "committed: $Message" }
            if ($Push) {
                git push
                if ($?) { Write-Host "pushed" }
            }
        }
    } finally {
        Pop-Location
    }
}
