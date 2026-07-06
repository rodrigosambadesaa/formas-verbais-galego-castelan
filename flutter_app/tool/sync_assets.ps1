$sourceDir = Resolve-Path "$PSScriptRoot\..\..\web-angular\src\assets\data"
$targetDir = Join-Path $PSScriptRoot "..\assets\data"
$targetDir = [System.IO.Path]::GetFullPath($targetDir)

if (-not (Test-Path $targetDir)) {
    New-Item -ItemType Directory -Path $targetDir | Out-Null
}

$files = @(
    "verbos_relacionados.tsv",
    "alineaciones_completas.tsv"
)

foreach ($file in $files) {
    $source = Join-Path $sourceDir $file
    if (Test-Path $source) {
        Copy-Item -LiteralPath $source -Destination (Join-Path $targetDir $file) -Force
        Write-Host "Copiado $file"
    }
    else {
        Write-Warning "No se encontró $source"
    }
}
