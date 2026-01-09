# PowerShell скрипт для перекомпіляції DLL

Write-Host "Перекомпіляція game_core.dll..." -ForegroundColor Cyan

$cppDir = "cpp_core"
$buildDir = "$cppDir\build"
$uiDir = "python_ui"

# Перевірка наявності cmake
$cmakePath = Get-Command cmake -ErrorAction SilentlyContinue
if (-not $cmakePath) {
    Write-Host "Помилка: cmake не знайдено! Встановіть CMake або використайте Visual Studio." -ForegroundColor Red
    exit 1
}

# Створення build директорії
if (-not (Test-Path $buildDir)) {
    New-Item -ItemType Directory -Path $buildDir | Out-Null
    Write-Host "Створено директорію $buildDir" -ForegroundColor Green
}

Push-Location $cppDir

try {
    # Конфігурація
    Write-Host "Конфігурація CMake..." -ForegroundColor Yellow
    & cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Помилка конфігурації CMake!" -ForegroundColor Red
        exit 1
    }
    
    # Збірка
    Write-Host "Збірка DLL..." -ForegroundColor Yellow
    & cmake --build build --config Release
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Помилка збірки!" -ForegroundColor Red
        exit 1
    }
    
    # Копіювання DLL
    $dllSource = "build\Release\game_core.dll"
    if (-not (Test-Path $dllSource)) {
        # Спробуємо Debug версію
        $dllSource = "build\Debug\game_core.dll"
    }
    
    if (Test-Path $dllSource) {
        $dllDest = "..\$uiDir\game_core.dll"
        Copy-Item -Path $dllSource -Destination $dllDest -Force
        Write-Host "DLL скопійовано до $dllDest" -ForegroundColor Green
        Write-Host "Готово! Тепер запустіть: python python_ui\app.py" -ForegroundColor Green
    } else {
        Write-Host "Помилка: DLL не знайдено після збірки!" -ForegroundColor Red
        exit 1
    }
} finally {
    Pop-Location
}

