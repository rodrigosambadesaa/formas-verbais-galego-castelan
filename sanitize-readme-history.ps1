$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $repoRoot

if (-not (Test-Path -LiteralPath '.git')) {
    throw 'Este script debe ejecutarse desde la raiz del repositorio.'
}

$originUrl = git remote get-url origin
if (-not $originUrl) {
    throw 'No se pudo obtener la URL remota de origin.'
}

$readmePath = Join-Path $repoRoot 'README.md'
if (-not (Test-Path -LiteralPath $readmePath)) {
    throw 'No existe README.md en la raiz del repositorio.'
}

$tempReadme = Join-Path ([System.IO.Path]::GetTempPath()) ("README-clean-" + [guid]::NewGuid().ToString() + ".md")
Copy-Item -LiteralPath $readmePath -Destination $tempReadme

try {
    git filter-repo --force --path README.md --invert-paths

    $cleanReadme = Get-Content -LiteralPath $tempReadme -Raw
    Set-Content -LiteralPath $readmePath -Value $cleanReadme -NoNewline

    git add README.md
    git commit -m "Add sanitized README.md"

    $hasOrigin = git remote
    if ($hasOrigin -notcontains 'origin') {
        git remote add origin $originUrl
    }

    git push origin --force --all
}
finally {
    if (Test-Path -LiteralPath $tempReadme) {
        Remove-Item -LiteralPath $tempReadme -Force
    }
}
