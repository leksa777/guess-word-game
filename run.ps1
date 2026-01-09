
param(
    [switch]$SkipBuild
)

Push-Location $PSScriptRoot
try {
    if (-not $SkipBuild) {
        if (Test-Path 'cpp_core') {
            Write-Host 'Building C++ core (cpp_core)...'
            cmake -S 'cpp_core' -B 'cpp_core\build' -DCMAKE_BUILD_TYPE=Release
            cmake --build 'cpp_core\build' --config Release
        } else {
            Write-Host "No 'cpp_core' directory found - skipping C++ build."
        }
    } else {
        Write-Host 'Skipping C++ build (user requested).'
    }

    $dllCandidates = @(
        [System.IO.Path]::Combine($PSScriptRoot, 'cpp_core', 'build', 'Release', 'game_core.dll'),
        [System.IO.Path]::Combine($PSScriptRoot, 'cpp_core', 'build', 'game_core.dll'),
        [System.IO.Path]::Combine($PSScriptRoot, 'cpp_core', 'game_core.dll')
    )

    $foundDll = $null
    foreach ($p in $dllCandidates) {
        if (Test-Path $p) { $foundDll = $p; break }
    }

    if (-not $foundDll) {
        Write-Error ('game_core.dll not found. Checked: {0}' -f ($dllCandidates -join ', '))
        Exit 1
    }

    $dest = Join-Path -Path $PSScriptRoot -ChildPath 'python_ui\game_core.dll'
    Write-Host ('Copying DLL from "{0}" to "{1}"' -f $foundDll, $dest)
    Copy-Item -Path $foundDll -Destination $dest -Force

    $pyRoot = Join-Path -Path $PSScriptRoot -ChildPath 'python_ui'
    $venvPath = Join-Path -Path $pyRoot -ChildPath '.venv'
    $venvPython = Join-Path -Path $venvPath -ChildPath 'Scripts\python.exe'

    if (-not (Test-Path $venvPython)) {
        Write-Host 'Creating Python virtual environment...'
        python -m venv $venvPath
    }

    Write-Host 'Installing Python dependencies (this may take a moment)...'
    & $venvPython -m pip install --upgrade pip
    & $venvPython -m pip install -r (Join-Path -Path $pyRoot -ChildPath 'requirements.txt')

    Write-Host 'Launching application...'
    Push-Location $pyRoot
    try {
        & $venvPython 'app.py'
    } finally {
        Pop-Location
    }

} finally {
    Pop-Location
}
