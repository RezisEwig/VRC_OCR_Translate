$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$modelDirectory = Join-Path $projectRoot "models"
$modelPath = Join-Path $modelDirectory "translategemma-4b-it.Q4_K_M.gguf"
$modelUrl = "https://huggingface.co/mradermacher/translategemma-4b-it-GGUF/resolve/main/translategemma-4b-it.Q4_K_M.gguf"
$modelSize = 2489909760L
$modelSha256 = "81200d03e843d2ec1ece6eeafe7d13cb6e5211e1fcd336ade55790b683a08330"

$runtimeDirectory = Join-Path $projectRoot "tools\llama.cpp\b9610"
$runtimeExe = Join-Path $runtimeDirectory "llama-server.exe"
$runtimeZip = Join-Path $projectRoot "tools\llama.cpp\llama-b9610-bin-win-vulkan-x64.zip"
$runtimeUrl = "https://github.com/ggml-org/llama.cpp/releases/download/b9610/llama-b9610-bin-win-vulkan-x64.zip"

function Invoke-CurlDownload {
    param(
        [Parameter(Mandatory = $true)][string]$Url,
        [Parameter(Mandatory = $true)][string]$Output,
        [switch]$Resume
    )
    $arguments = @("-L", "--fail", "--retry", "3", "--show-error")
    if ($Resume) {
        $arguments += @("--continue-at", "-")
    }
    $arguments += @("--output", $Output, $Url)
    & curl.exe @arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Download failed: $Url"
    }
}

New-Item -ItemType Directory -Force -Path $modelDirectory | Out-Null
if (Test-Path -LiteralPath $modelPath) {
    $length = (Get-Item -LiteralPath $modelPath).Length
    if ($length -gt $modelSize) {
        $stream = [System.IO.File]::Open($modelPath, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Write)
        try {
            $stream.SetLength($modelSize)
        }
        finally {
            $stream.Dispose()
        }
    }
}

if (-not (Test-Path -LiteralPath $modelPath) -or (Get-Item -LiteralPath $modelPath).Length -lt $modelSize) {
    Write-Host "Downloading TranslateGemma model..."
    Invoke-CurlDownload -Url $modelUrl -Output $modelPath -Resume
}
if ((Get-Item -LiteralPath $modelPath).Length -ne $modelSize) {
    throw "TranslateGemma model size is invalid. Delete the model file and run setup again."
}

Write-Host "Verifying TranslateGemma SHA-256..."
$actualHash = (Get-FileHash -LiteralPath $modelPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualHash -ne $modelSha256) {
    throw "TranslateGemma SHA-256 mismatch. Delete the model file and run setup again."
}

if (-not (Test-Path -LiteralPath $runtimeExe)) {
    Write-Host "Downloading llama.cpp Vulkan runtime..."
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $runtimeZip) | Out-Null
    Invoke-CurlDownload -Url $runtimeUrl -Output $runtimeZip
    New-Item -ItemType Directory -Force -Path $runtimeDirectory | Out-Null
    Expand-Archive -LiteralPath $runtimeZip -DestinationPath $runtimeDirectory -Force
    Remove-Item -LiteralPath $runtimeZip -Force
}
if (-not (Test-Path -LiteralPath $runtimeExe)) {
    throw "llama-server.exe was not installed correctly."
}

Write-Host "Model and Vulkan runtime are ready."
